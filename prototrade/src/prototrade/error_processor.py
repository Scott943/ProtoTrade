from threading import Thread
from models.error_event import ErrorEvent

class ErrorProcessor:
    def __init__(self, error_queue, SENTINEL):
        self._error_queue = error_queue
        self._create_thread_to_process_errors()
        self._SENTINEL = SENTINEL
    
    def _create_thread_to_process_errors(self):
        self._error_processing_thread = Thread(
            target=self._process_errors)

        self._error_processing_thread.start()

    def _process_errors(self):
        while True:
            event = self._error_queue.get()

            if event == self._SENTINEL:
                break

            raise event.exception #re-raise the exception in the main_program

        print("Subscription queue reader finished")

    def stop_queue_polling(self):
            # self._subscription_queue.close()
        if self._error_processing_thread:
            # Inform consumer thread to stop
            self._error_queue.put(self._SENTINEL)
            self._error_processing_thread.join()
