"""
Debugging utilities for constructs
"""

import sys
import traceback
import pdb
import inspect

from construct import *
from construct.lib import *


class Probe(Construct):
    r"""
    A probe: dumps the context, stack frames, and stream content to the screen to aid the debugging process.

    :param name: the display name
    :param show_stream: whether or not to show stream contents. default is True. the stream must be seekable.
    :param show_context: whether or not to show the context. default is True.
    :param show_stack: whether or not to show the upper stack frames. default is True.
    :param stream_lookahead: the number of bytes to dump when show_stack is set. default is 100.
    
    Example::
        >>> (Byte >> Probe() >> Byte).build([1,2])

        ================================================================================
        Probe <unnamed 2>
        Container: 
            stream_position = 1
            following_stream_data = EOF reached
            context = Container: 
            stack = ListContainer: 
                Container: 
                    obj = [1, 2]
                    context = None
                    stream = <_io.BytesIO object at 0x7f32d5fce990>
                    self = <Sequence: None>
                    kw = {}
                Container: 
                    obj = [1, 2]
                    context = Container: 
                    stream = <_io.BytesIO object at 0x7f32d5fce990>
                    self = <Sequence: None>
                    kw = {}
                Container: 
                    obj = [1, 2]
                    context = Container: 
                    subobj = 2
                    i = 1
                    buildret = None
                    sc = Probe('<unnamed 2>')
                    stream = <_io.BytesIO object at 0x7f32d5fce990>
                    objiter = <list_iterator object at 0x7f32da018400>
                    self = <Sequence: None>
                Container: 
                    obj = 2
                    context = Container: 
                    stream = <_io.BytesIO object at 0x7f32d5fce990>
                    self = Probe('<unnamed 2>')
        ================================================================================
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
          File "/home/arkadiusz/Dokumenty/GitHub/construct/construct/core.py", line 218, in build
            self.build_stream(obj, stream, context, **kw)
          File "/home/arkadiusz/Dokumenty/GitHub/construct/construct/core.py", line 230, in build_stream
            self._build(obj, stream, context)
          File "/home/arkadiusz/Dokumenty/GitHub/construct/construct/core.py", line 925, in _build
            subobj = next(objiter)
        StopIteration
    """
    __slots__ = ["printname", "show_stream", "show_context", "show_stack", "stream_lookahead"]
    counter = 0
    
    def __init__(self, name=None, show_stream=True, show_context=True, show_stack=True, stream_lookahead=128):
        super(Probe, self).__init__()
        if name is None:
            Probe.counter += 1
            name = "<unnamed %d>" % Probe.counter
        self.printname = name
        self.show_stream = show_stream
        self.show_context = show_context
        self.show_stack = show_stack
        self.stream_lookahead = stream_lookahead
        self.flagbuildnone = True
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.printname)
    def _parse(self, stream, context):
        self.printout(stream, context)
    def _build(self, obj, stream, context):
        self.printout(stream, context)
    def _sizeof(self, context):
        return 0
    
    def printout(self, stream, context):
        print("================================================================================")
        print("Probe %s" % self.printname)

        if self.show_stream:
            fallback = stream.tell()
            datafollows = stream.read(self.stream_lookahead)
            stream.seek(fallback)
            if not datafollows:
                print("EOF reached")
            else:
                print(hexdump(datafollows, 32))
        
        if self.show_context:
            print(context)
        
        # if self.show_stack:
        #     stack = ListContainer()
        #     print("Stack: ")
        #     frames = [s[0] for s in inspect.stack()][1:-1]
        #     for f in reversed(frames):
        #         a = Container()
        #         a.__update__(f.f_locals)
        #         stack.append(a)
        #         # print(f.f_locals)
        #     print(stack)
        
        print("================================================================================")


class Debugger(Subconstruct):
    r"""
    A pdb-based debugger. When an exception occurs in the subcon, a debugger will appear and allow you to debug the error (and even fix it on-the-fly).
    
    :param subcon: the subcon to debug
    
    Example::
    
        >>> Debugger(Byte[3]).build([])
        ================================================================================
        Debugging exception of <Range: None>:
          File "/home/arkadiusz/Dokumenty/GitHub/construct/construct/debug.py", line 116, in _build
            obj.stack.append(a)
          File "/home/arkadiusz/Dokumenty/GitHub/construct/construct/core.py", line 1069, in _build
            raise RangeError("expected from %d to %d elements, found %d" % (self.min, self.max, len(obj)))
        construct.core.RangeError: expected from 3 to 3 elements, found 0

        > /home/arkadiusz/Dokumenty/GitHub/construct/construct/core.py(1069)_build()
        -> raise RangeError("expected from %d to %d elements, found %d" % (self.min, self.max, len(obj)))
        (Pdb) 
        ================================================================================
    """
    __slots__ = ["retval"]
    def _parse(self, stream, context):
        try:
            return self.subcon._parse(stream, context)
        except Exception:
            self.retval = NotImplemented
            self.handle_exc("(you can set the value of 'self.retval', which will be returned)")
            if self.retval is NotImplemented:
                raise
            else:
                return self.retval
    def _build(self, obj, stream, context):
        try:
            self.subcon._build(obj, stream, context)
        except Exception:
            self.handle_exc()
    def handle_exc(self, msg = None):
        print("================================================================================")
        print("Debugging exception of %s:" % (self.subcon,))
        print("".join(traceback.format_exception(*sys.exc_info())[1:]))
        if msg:
            print(msg)
        pdb.post_mortem(sys.exc_info()[2])
        print("================================================================================")

