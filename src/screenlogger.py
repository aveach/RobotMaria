class ScreenLogger:
    def __init__(self, loghandler=None, verbose = True):
        self.LogMessage = None
        self.LogHandler = loghandler
        self.Verbose = verbose
        return
    def Log(self, message):
        if self.LogMessage != message:
            self.LogMessage = message
            if self.LogHandler != None:
                self.LogHandler(self.LogMessage)
            if self.Verbose:
                print self.LogMessage
        return
