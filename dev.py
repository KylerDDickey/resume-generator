from argparse import ArgumentParser
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from queue import Full, Queue
from subprocess import DEVNULL, STDOUT, Popen
from threading import Event, Lock, Thread
from typing import Callable, Protocol, Set, TypeVar
from tomllib import load as load_toml

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from websockets.exceptions import ConnectionClosedOK
from websockets.sync.server import ServerConnection, serve as serve_websocket

Callback = Callable[[], None]


class Daemon(Protocol):

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def join(self) -> None:
        ...


class Legion(Daemon):

    def __init__(self, *daemons: Daemon) -> None:
        self._daemons = daemons

    def start(self) -> None:
        for d in self._daemons:
            d.start()

    def stop(self) -> None:
        for d in self._daemons:
            d.stop()

    def join(self) -> None:
        for d in self._daemons:
            d.join()


class ProcessFactory(Protocol):

    def create(self) -> Popen:
        ...


class ProcessRequest(Protocol):

    pass


class NoProcessRequest(ProcessRequest):

    pass


class CreateProcessRequest(ProcessRequest):

    def __init__(self, process_factory: ProcessFactory) -> None:
        self._process_factory = process_factory

    def factory(self) -> ProcessFactory:
        return self._process_factory


@dataclass
class BuildProcessRequestQueueOptions:
    max_queue_size: int


class BuildProcessRequestQueue:

    def __init__(
        self, process_factory: ProcessFactory,
        build_process_request_queue_options: BuildProcessRequestQueueOptions
    ) -> None:
        max_queue_size = build_process_request_queue_options.max_queue_size

        self._process_factory = process_factory
        self._queue: Queue[ProcessRequest] = Queue(max_queue_size)

    def put_create_process(self) -> None:
        try:
            self._queue.put(CreateProcessRequest(self._process_factory))
        except Full as f:
            print(f)

    def put_no_process(self) -> None:
        try:
            self._queue.put_nowait(NoProcessRequest())
        except Full as f:
            print(f)

    def get(self) -> ProcessRequest:
        try:
            return self._queue.get()
        finally:
            self._queue.task_done()

    def join(self) -> None:
        self._queue.join()
        print('test')


@dataclass
class ProjectDirObserverDaemonOptions:
    targets_to_watch: Set[str]


class ProjectDirObserverDaemon(Daemon):

    def __init__(
            self, file_system_event_handler: FileSystemEventHandler,
            project_dir_observer_options: ProjectDirObserverDaemonOptions
    ) -> None:
        targets_to_watch = project_dir_observer_options.targets_to_watch
        if len(targets_to_watch) == 0:
            raise ValueError('''
                No project directory targets were specified. File system events
                will not trigger behaviors defined in the FileSystemEventHandler
                implementation. Closing...
            ''')

        observer = Observer()
        for target in targets_to_watch:
            observer.schedule(
                file_system_event_handler,
                target,
                recursive=True,
            )
        self._observer = observer

    def start(self) -> None:
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()

    def join(self) -> None:
        self._observer.join()


class BuildProcessRequestQueueReader:

    def __init__(self, build_process_request_queue: BuildProcessRequestQueue,
                 on_process_success: Callback) -> None:

        self._shudown = Event()

        self._process_not_running = Event()
        self._process_not_running.set()

        self._thread_not_created = Event()
        self._thread_not_created.set()

        self._build_process_request_queue = build_process_request_queue

        def create_thread_target(process_factory: ProcessFactory) -> Callback:

            def thread_logic() -> None:
                print('running')
                self._build_process_request_queue.join()
                self._process_not_running.clear()

                try:
                    proc = process_factory.create()
                    return_code = proc.wait()
                    if return_code != 0:
                        return

                    print('build complete')
                    on_process_success()
                finally:
                    self._thread_not_created.set()
                    self._process_not_running.set()

            return thread_logic

        self._create_thread_target = create_thread_target

    def handle_request(self) -> None:
        request = self._build_process_request_queue.get()
        match request:
            case CreateProcessRequest() as c:
                if not self._thread_not_created.is_set():
                    print('skip')
                    return

                self._process_not_running.wait()
                self._thread_not_created.clear()

                target = self._create_thread_target(c.factory())
                Thread(target=target).start()
            case NoProcessRequest():
                return
            case _:
                raise AssertionError('''
                    A case for given implementation of ProcessRequest has no
                    definition in BuildProcessRequestQueueReader.handle_request.
                    All implementations of ProcessRequest must be handled.
                ''')

    def serve_forever(self) -> None:
        self._shudown.clear()
        while not self._shudown.is_set():
            self.handle_request()

    def shutdown(self) -> None:
        self._shudown.set()
        self._build_process_request_queue.put_no_process()


class BuildProcessRequestQueueReaderDaemon(Daemon):

    def __init__(
        self,
        build_process_request_queue_reader: BuildProcessRequestQueueReader
    ) -> None:
        self._build_process_request_queue_reader = build_process_request_queue_reader
        self._stop = Event()

        def serve_build_requests():
            while not self._stop.is_set():
                try:
                    self._build_process_request_queue_reader.serve_forever()
                except Exception as e:
                    print(e)

        self._thread = Thread(target=serve_build_requests)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        if self._stop.is_set():
            return

        self._stop.set()
        self._build_process_request_queue_reader.shutdown()

    def join(self) -> None:
        self._thread.join()


@dataclass
class DevHTTPServerDaemonOptions:
    static_directory: str
    host: str
    port: int


class DevHTTPServerDaemon(Daemon):

    def __init__(
            self, dev_http_server_daemon_options: DevHTTPServerDaemonOptions
    ) -> None:
        static_directory = dev_http_server_daemon_options.static_directory
        host = dev_http_server_daemon_options.host
        port = dev_http_server_daemon_options.port

        class DevServerHandler(SimpleHTTPRequestHandler):

            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, directory=static_directory, **kwargs)

            def end_headers(self):
                self.send_header("Cache-Control",
                                 "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                super().end_headers()

        # We use a threading HTTP server because Chromium-based browsers
        # appear to hang otherwise.
        server_address = (host, port)
        self._http_server = ThreadingHTTPServer(server_address,
                                                DevServerHandler)
        self._stop = Event()

        def serve_http_requests() -> None:
            while not self._stop.is_set():
                try:
                    self._http_server.serve_forever()
                except Exception as e:
                    print(e)

        self._thread = Thread(target=serve_http_requests)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        if self._stop.is_set():
            return

        self._stop.set()
        self._http_server.shutdown()

    def join(self) -> None:
        self._thread.join()


class WebSocketMessagePublisher:

    def __init__(self) -> None:
        self._lock = Lock()
        self._broadcast_event = Event()
        self._subscribers: Set[ServerConnection] = set()

    def add(self, new_sub: ServerConnection) -> None:
        with self._lock:
            print('new connection')
            self._subscribers.add(new_sub)

    def remove(self, sub: ServerConnection) -> None:
        with self._lock:
            print('connection removed')
            self._subscribers.remove(sub)

    def broadcast(self, message: str) -> None:
        with self._lock:
            self._broadcast_event.set()
            for s in self._subscribers:
                s.send(message)
            self._broadcast_event.clear()

    def close_all(self) -> None:
        with self._lock:
            for s in self._subscribers:
                s.close()


@dataclass
class DevWebSocketServerDaemonOptions:
    host: str
    port: int


class DevWebSocketServerDaemon(Daemon):

    def __init__(
        self, web_socket_message_publisher: WebSocketMessagePublisher,
        dev_web_socket_server_daemon_options: DevWebSocketServerDaemonOptions
    ) -> None:
        self._stop = Event()

        def handler(websocket: ServerConnection):
            web_socket_message_publisher.add(websocket)

            try:
                # This is broken when one connection refreshes
                # more than once
                data = websocket.recv()
                if data == 'close':
                    websocket.close()

                if self._stop.is_set():
                    return
            except ConnectionClosedOK:
                print('closed ok')
            finally:
                web_socket_message_publisher.remove(websocket)

        host = dev_web_socket_server_daemon_options.host
        port = dev_web_socket_server_daemon_options.port

        self._web_socket_server = serve_websocket(handler,
                                                  host=host,
                                                  port=port)

        def serve_wc_requests() -> None:
            while not self._stop.is_set():
                try:
                    self._web_socket_server.serve_forever()
                except Exception as e:
                    print(e)

        def close_all_connections() -> None:
            web_socket_message_publisher.close_all()

        self._close_all_connections = close_all_connections
        self._thread = Thread(target=serve_wc_requests)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        if self._stop.is_set():
            return

        self._stop.set()
        self._close_all_connections()
        self._web_socket_server.shutdown()

    def join(self) -> None:
        self._thread.join()


@dataclass
class DaemonOptions:
    build_process_request_queue_options: BuildProcessRequestQueueOptions
    project_dir_observer_daemon_options: ProjectDirObserverDaemonOptions
    dev_http_server_daemon_options: DevHTTPServerDaemonOptions
    dev_web_socket_server_daemon_options: DevWebSocketServerDaemonOptions


@dataclass
class WebSocketBroadcastMessages:
    on_process_success_message: str


@dataclass
class ProcessConfig:
    stdout: int
    stderr: int


@dataclass
class Config:
    daemon_options: DaemonOptions
    process_config: ProcessConfig
    web_socket_broadcast_messages: WebSocketBroadcastMessages


def read_config(optional_file_name: str | None) -> Config:

    def read_config_file(file_name: str) -> dict:
        with open(file_name, 'rb') as config_file:
            return load_toml(config_file)

    V = TypeVar("V")

    def coalesce(input: V | None, default: V) -> V:
        return input if not input is None else default

    d = {} if optional_file_name is None else read_config_file(
        optional_file_name)

    raw_build_process_request_queue_options = coalesce(
        d.get('build_process_request_queue'), {})
    raw_project_dir_observer_options = coalesce(d.get('project_dir_observer'),
                                                {})
    raw_local_web_server = coalesce(d.get('local_web_server'), {})
    daemon_options = DaemonOptions(
        BuildProcessRequestQueueOptions(
            coalesce(
                raw_build_process_request_queue_options.get('max_queue_size'),
                100)),
        ProjectDirObserverDaemonOptions(
            set(
                coalesce(
                    raw_project_dir_observer_options.get('targets_to_watch'), [
                        './conversion', './styling', './templates', './data',
                        './main.py'
                    ]))),
        DevHTTPServerDaemonOptions(
            coalesce(raw_local_web_server.get('static_directory'),
                     './static/'),
            coalesce(raw_local_web_server.get('host'), ''),
            coalesce(raw_local_web_server.get('http_port'), 8080)),
        DevWebSocketServerDaemonOptions(
            coalesce(raw_local_web_server.get('host'), ''),
            coalesce(raw_local_web_server.get('ws_port'), 8081)))

    def match_str_to_stdio(stdio_str: str | None) -> int:
        match coalesce(stdio_str, '').strip().upper():
            case 'STDOUT':
                return STDOUT
            case 'DEVNULL':
                return DEVNULL
            case _:
                return DEVNULL

    raw_process_config = coalesce(d.get('process_config'), {})
    process_config = ProcessConfig(
        match_str_to_stdio(raw_process_config.get('stdout')),
        match_str_to_stdio(raw_process_config.get('stderr')))

    raw_web_socket_broadcast_messages = coalesce(
        raw_local_web_server.get('broadcast_messages'), {})
    web_socket_broadcast_messages = WebSocketBroadcastMessages(
        coalesce(raw_web_socket_broadcast_messages.get('on_process_success'),
                 'reload'))

    return Config(daemon_options, process_config,
                  web_socket_broadcast_messages)


def get_daemons(data_source: str, config: Config) -> Daemon:
    daemon_options = config.daemon_options
    process_config = config.process_config
    web_socket_broadcast_messages = config.web_socket_broadcast_messages

    trimmed_data_source = data_source.strip()

    class MakeProcessFactory(ProcessFactory):

        def create(self) -> Popen:
            return Popen(['make', 'pdf-dev', f'data={trimmed_data_source}'],
                         stdout=process_config.stdout,
                         stderr=process_config.stderr)

    make_process_factory = MakeProcessFactory()
    build_process_request_queue = BuildProcessRequestQueue(
        make_process_factory,
        daemon_options.build_process_request_queue_options)

    class RebuildEventHandler(FileSystemEventHandler):

        def on_modified(self, event: FileSystemEvent) -> None:
            if event.is_directory:
                return

            print(event)
            build_process_request_queue.put_create_process()

    rebuild_event_handler = RebuildEventHandler()

    project_dir_observer_daemon = ProjectDirObserverDaemon(
        rebuild_event_handler,
        daemon_options.project_dir_observer_daemon_options)

    web_socket_message_publisher = WebSocketMessagePublisher()

    build_process_request_queue_reader = BuildProcessRequestQueueReader(
        build_process_request_queue, lambda: web_socket_message_publisher.
        broadcast(web_socket_broadcast_messages.on_process_success_message))

    build_process_request_queue_reader_daemon = BuildProcessRequestQueueReaderDaemon(
        build_process_request_queue_reader)

    dev_http_server_daemon = DevHTTPServerDaemon(
        daemon_options.dev_http_server_daemon_options)

    dev_web_socket_server_daemon = DevWebSocketServerDaemon(
        web_socket_message_publisher,
        daemon_options.dev_web_socket_server_daemon_options)

    return Legion(project_dir_observer_daemon,
                  build_process_request_queue_reader_daemon,
                  dev_http_server_daemon, dev_web_socket_server_daemon)


@contextmanager
def manage_daemon(daemon: Daemon):
    waiter = Event()

    def wait_for_signals():
        try:
            waiter.wait()
        except KeyboardInterrupt:
            waiter.set()

    def try_tear_down():
        try:
            daemon.stop()
            daemon.join()
            waiter.clear()
        except KeyboardInterrupt:
            pass

    try:
        daemon.start()
        yield wait_for_signals
    finally:
        while waiter.is_set():
            try_tear_down()


def get_arg_parser() -> ArgumentParser:
    prog = "Resume Generator Dev Server"
    description = '''
    A hot-reloading server that shows the resulting resume after changes to the
    template and the driver data live in a browser.
    '''
    parser = ArgumentParser(prog=prog, description=description)

    data_file_help = '''
    The file containing JSON-formatted driver data.
    '''
    parser.add_argument('data_source',
                        metavar='DATA_SOURCE',
                        type=str,
                        help=data_file_help)

    config_file_help = '''
    The options that adjust the options for the daemons and the
    process and inter-thread communication components.
    '''
    parser.add_argument('-c',
                        '--config',
                        dest='config_file',
                        type=str,
                        required=False,
                        help=config_file_help)

    return parser


def main() -> None:
    parser = get_arg_parser()
    args = parser.parse_args()

    data_source = args.data_source
    config = read_config(args.config_file)
    with manage_daemon(get_daemons(data_source, config)) as manage:
        manage()


if __name__ == "__main__":
    main()
