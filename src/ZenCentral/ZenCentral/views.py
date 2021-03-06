from LibLisa import blockProfiler, lastCallProfile
from rest_framework import viewsets

class profiledModelViewSet(viewsets.ModelViewSet):
    """
    An enhanced version of viewset base class(viewsets.ModelViewSet).

    Any viewset derived from this will also return runtime profiling information
    of the call.
    """
    def dispatch(self, *kwargs, **initkwargs):
        with blockProfiler("view.dispatch"):
            retval = super().dispatch(*kwargs, **initkwargs)

        try:
            retval.data["CallProfile"] = lastCallProfile(True)
            # retval.data.move_to_end("CallProfile", last=False)
        except:
            pass
        return retval
