import sys
from datetime import datetime
from typing import Optional

        
class BiliLogger:
    __slots__ = ()

    # 格式化数据
    @staticmethod
    def format(
            *objects,
            extra_info: Optional[str] = None,
            need_timestamp: bool = True):
        timestamp = f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}]' if need_timestamp else '>'
        extra_info = f' ({extra_info})' if extra_info is not None else ''
        if objects:
            first_value, *others = objects
            others = [f'# {i}' for i in others]
            return f'{timestamp} {first_value}{extra_info}', *others
        return f'{timestamp} NULL{extra_info}',

    def info(
            self,
            *objects,
            extra_info: Optional[str] = None,
            need_timestamp: bool = True):
        texts = self.format(
            *objects,
            extra_info=extra_info,
            need_timestamp=need_timestamp)
        for i in texts:
            print(i)

    def warn(
            self,
            *objects,
            extra_info: Optional[str] = None):
        texts = self.format(
            *objects,
            extra_info=extra_info,
            need_timestamp=True)
        for i in texts:
            print(i, file=sys.stderr)
        
        with open('bili.log', 'a', encoding='utf-8') as f:
            for i in texts:
                f.write(f'{i}\n')

    def debug(
            self,
            *objects,
            **kwargs):
        self.warn(*objects, **kwargs)

    def error(
            self,
            *objects,
            **kwargs):
        self.warn(*objects, **kwargs)
        sys.exit(-1)
  

printer = BiliLogger()

           
def info(*objects, **kwargs):
    printer.info(*objects, **kwargs)


def warn(*objects, **kwargs):
    printer.warn(*objects, **kwargs)


def error(*objects, **kwargs):
    printer.error(*objects, **kwargs)


def debug(*objects, **kwargs):
    printer.debug(*objects, **kwargs)
