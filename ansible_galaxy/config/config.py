

class Config(object):
    def __init__(self):
        self.defaults = {}
        self.servers = []
        self.content_roots = []
        self.options = {}

    def as_dict(self):
        return {
            'defaults': self.defaults,
            'servers': self.servers,
            'content_roots': self.content_roots,
            'options': self.options,
        }

    @classmethod
    def from_dict(cls, data):
        inst = cls()
        inst.defaults = data.get('defaults', inst.defaults)
        inst.servers = data.get('servers', inst.servers)
        inst.content_roots = data.get('content_roots', inst.content_roots)
        inst.options = data.get('options', inst.options)
        return inst
