class BoundedTextLimits:
    
    def __init__(self, char_limit: int):
        self.__char_limit = char_limit


    def char_limit(self) -> int:
        return max(self.__char_limit, 0)


class BoundedText:

    def __init__(self, limits: BoundedTextLimits, value: str):
        self.__limits = limits
        self.__value = value

    def to_string(self) -> str:
        trimmed = self.__value.strip()
        limit = min(self.__limits.char_limit(), len(trimmed))
        return trimmed[0:limit]

