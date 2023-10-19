import inspect
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import background_tasks, globals, helpers  # pylint: disable=redefined-builtin
from .logging import log
from .native import Native
from .observables import ObservableSet
from .storage import Storage


class State(Enum):
    STOPPED = 0
    STARTING = 1
    STARTED = 2
    STOPPING = 3


class App(FastAPI):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.native = Native()
        self.storage = Storage()
        self.urls = ObservableSet()
        self.state: State = State.STOPPED

        self._startup_handlers: List[Union[Callable[..., Any], Awaitable]] = []
        self._shutdown_handlers: List[Union[Callable[..., Any], Awaitable]] = []
        self._connect_handlers: List[Union[Callable[..., Any], Awaitable]] = []
        self._disconnect_handlers: List[Union[Callable[..., Any], Awaitable]] = []
        self._exception_handlers: List[Callable[..., Any]] = [log.exception]

    @property
    def is_starting(self) -> bool:
        """Return whether NiceGUI is starting."""
        return self.state == State.STARTING

    @property
    def is_started(self) -> bool:
        """Return whether NiceGUI is started."""
        return self.state == State.STARTED

    @property
    def is_stopping(self) -> bool:
        """Return whether NiceGUI is stopping."""
        return self.state == State.STOPPING

    @property
    def is_stopped(self) -> bool:
        """Return whether NiceGUI is stopped."""
        return self.state == State.STOPPED

    def start(self) -> None:
        """Start NiceGUI. (For internal use only.)"""
        self.state = State.STARTING
        with globals.index_client:
            for t in self._startup_handlers:
                helpers.safe_invoke(t)
        self.state = State.STARTED

    def stop(self) -> None:
        """Stop NiceGUI. (For internal use only.)"""
        self.state = State.STOPPING
        with globals.index_client:
            for t in self._shutdown_handlers:
                helpers.safe_invoke(t)
        self.state = State.STOPPED

    def on_connect(self, handler: Union[Callable, Awaitable]) -> None:
        """Called every time a new client connects to NiceGUI.

        The callback has an optional parameter of `nicegui.Client`.
        """
        self._connect_handlers.append(handler)

    def on_disconnect(self, handler: Union[Callable, Awaitable]) -> None:
        """Called every time a new client disconnects from NiceGUI.

        The callback has an optional parameter of `nicegui.Client`.
        """
        self._disconnect_handlers.append(handler)

    def on_startup(self, handler: Union[Callable, Awaitable]) -> None:
        """Called when NiceGUI is started or restarted.

        Needs to be called before `ui.run()`.
        """
        if self.is_started:
            raise RuntimeError('Unable to register another startup handler. NiceGUI has already been started.')
        self._startup_handlers.append(handler)

    def on_shutdown(self, handler: Union[Callable, Awaitable]) -> None:
        """Called when NiceGUI is shut down or restarted.

        When NiceGUI is shut down or restarted, all tasks still in execution will be automatically canceled.
        """
        self._shutdown_handlers.append(handler)

    def on_exception(self, handler: Callable) -> None:
        """Called when an exception occurs.

        The callback has an optional parameter of `Exception`.
        """
        self._exception_handlers.append(handler)

    def handle_exception(self, exception: Exception) -> None:
        """Handle an exception by invoking all registered exception handlers."""
        for handler in self._exception_handlers:
            result = handler() if not inspect.signature(handler).parameters else handler(exception)
            if helpers.is_coroutine_function(handler):
                background_tasks.create(result)

    def shutdown(self) -> None:
        """Shut down NiceGUI.

        This will programmatically stop the server.
        Only possible when auto-reload is disabled.
        """
        if globals.reload:
            raise RuntimeError('calling shutdown() is not supported when auto-reload is enabled')
        if self.native.main_window:
            self.native.main_window.destroy()
        else:
            globals.server.should_exit = True

    def add_static_files(self, url_path: str, local_directory: Union[str, Path]) -> None:
        """Add a directory of static files.

        `add_static_files()` makes a local directory available at the specified endpoint, e.g. `'/static'`.
        This is useful for providing local data like images to the frontend.
        Otherwise the browser would not be able to access the files.
        Do only put non-security-critical files in there, as they are accessible to everyone.

        To make a single file accessible, you can use `add_static_file()`.
        For media files which should be streamed, you can use `add_media_files()` or `add_media_file()` instead.

        :param url_path: string that starts with a slash "/" and identifies the path at which the files should be served
        :param local_directory: local folder with files to serve as static content
        """
        if url_path == '/':
            raise ValueError('''Path cannot be "/", because it would hide NiceGUI's internal "/_nicegui" route.''')
        self.mount(url_path, StaticFiles(directory=str(local_directory)))

    def add_static_file(self, *,
                        local_file: Union[str, Path],
                        url_path: Optional[str] = None,
                        single_use: bool = False,
                        ) -> str:
        """Add a single static file.

        Allows a local file to be accessed online with enabled caching.
        If `url_path` is not specified, a path will be generated.

        To make a whole folder of files accessible, use `add_static_files()` instead.
        For media files which should be streamed, you can use `add_media_files()` or `add_media_file()` instead.

        :param local_file: local file to serve as static content
        :param url_path: string that starts with a slash "/" and identifies the path at which the file should be served (default: None -> auto-generated URL path)
        :param single_use: whether to remove the route after the file has been downloaded once (default: False)
        :return: URL path which can be used to access the file
        """
        file = Path(local_file).resolve()
        if not file.is_file():
            raise ValueError(f'File not found: {file}')
        path = f'/_nicegui/auto/static/{helpers.hash_file_path(file)}/{file.name}' if url_path is None else url_path

        @self.get(path)
        def read_item() -> FileResponse:
            if single_use:
                self.remove_route(path)
            return FileResponse(file, headers={'Cache-Control': 'public, max-age=3600'})

        return path

    def add_media_files(self, url_path: str, local_directory: Union[str, Path]) -> None:
        """Add directory of media files.

        `add_media_files()` allows a local files to be streamed from a specified endpoint, e.g. `'/media'`.
        This should be used for media files to support proper streaming.
        Otherwise the browser would not be able to access and load the the files incrementally or jump to different positions in the stream.
        Do only put non-security-critical files in there, as they are accessible to everyone.

        To make a single file accessible via streaming, you can use `add_media_file()`.
        For small static files, you can use `add_static_files()` or `add_static_file()` instead.

        :param url_path: string that starts with a slash "/" and identifies the path at which the files should be served
        :param local_directory: local folder with files to serve as media content
        """
        @self.get(url_path + '/{filename:path}')
        def read_item(request: Request, filename: str) -> StreamingResponse:
            filepath = Path(local_directory) / filename
            if not filepath.is_file():
                raise HTTPException(status_code=404, detail='Not Found')
            return helpers.get_streaming_response(filepath, request)

    def add_media_file(self, *,
                       local_file: Union[str, Path],
                       url_path: Optional[str] = None,
                       single_use: bool = False,
                       ) -> str:
        """Add a single media file.

        Allows a local file to be streamed.
        If `url_path` is not specified, a path will be generated.

        To make a whole folder of media files accessible via streaming, use `add_media_files()` instead.
        For small static files, you can use `add_static_files()` or `add_static_file()` instead.

        :param local_file: local file to serve as media content
        :param url_path: string that starts with a slash "/" and identifies the path at which the file should be served (default: None -> auto-generated URL path)
        :param single_use: whether to remove the route after the media file has been downloaded once (default: False)
        :return: URL path which can be used to access the file
        """
        file = Path(local_file).resolve()
        if not file.is_file():
            raise ValueError(f'File not found: {local_file}')
        path = f'/_nicegui/auto/media/{helpers.hash_file_path(file)}/{file.name}' if url_path is None else url_path

        @self.get(path)
        def read_item(request: Request) -> StreamingResponse:
            if single_use:
                self.remove_route(path)
            return helpers.get_streaming_response(file, request)

        return path

    def remove_route(self, path: str) -> None:
        """Remove routes with the given path."""
        self.routes[:] = [r for r in self.routes if getattr(r, 'path', None) != path]
