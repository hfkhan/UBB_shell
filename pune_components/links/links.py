from pynsim import Link


class PuneLink(Link):
    description = "Common Methods for Pune Links"

    def __init__(self, name, **kwargs):
        super(PuneLink, self).__init__(name, **kwargs)
        self.institution_names = []
        self.flow=0

    _properties = {'flow': None,
                   }


    def add_to_institutions(self, institution_list, n):

        for institution in n.institutions:
            for inst_name in institution_list:
                if institution.name.lower() == inst_name.lower():
                    institution.add_link(self)


class River(PuneLink):
    pass

class Pipeline(PuneLink):
    pass

class Canal(PuneLink):
    pass