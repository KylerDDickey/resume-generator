(() => {
  const port = 8081;
  const socketUrl = `ws://localhost:${port}`;

  const socket = new WebSocket(socketUrl);
  socket.addEventListener("message", (event) => {
    console.log(event);

    if (event.data === "reload") {
      socket.send("close");
    }
  });
  socket.addEventListener("close", (event) => {
    console.log(event);
    socket.send("close");
    location.reload();
  });
})();
