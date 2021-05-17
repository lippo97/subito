class Announcer():

    def _do_nothing(*args):
        pass

    def __init__(self, on_new = _do_nothing, on_receive_update = _do_nothing, initial = []):
        self._on_new = on_new
        self._on_receive_update = on_receive_update
        self._old = initial

    def submit(self, update):
        self._on_receive_update(update)
        new_items = self._new_items(update)
        if new_items:
            self._replace_old(update)
            self._on_new(new_items, update)

    def _new_items(self, update):
        slice_index = 0
        for item in self._old:
            try:
                slice_index = update.index(item)
                break
            except ValueError:
                pass
        return update[:slice_index]

    def _replace_old(self, update):
        self._old = update