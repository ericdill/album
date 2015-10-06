import flask
import uuid
from bokeh.exceptions import DataIntegrityException
from bokeh.server.views.main import _makedoc

class BokehBlueprint(flask.Blueprint):

    def __init__(self, *args, **kwargs):
        super(BokehBlueprint, self).__init__(*args, **kwargs)
        self.debugjs = None

    def setup(self, backend, backbone_storage, servermodel_storage,
              authentication):
        self.backend = backend
        self.backbone_storage = backbone_storage
        self.servermodel_storage = servermodel_storage
        # self.authentication = authentication
        self.bokehjsdir = settings.bokehjsdir()
        self.bokehjssrcdir = settings.bokehjssrcdir()

    # def current_user(self):
    #     return self.authentication.current_user()

    def js_files(self):
        bokehjsdir = self.bokehjsdir
        js_files = []
        for root, dirnames, files in walk(bokehjsdir):
            for fname in files:
                if fname.endswith(".js") and 'vendor' not in root:
                    js_files.append(join(root, fname))
        return js_files


bokeh_app = BokehBlueprint(
    'album.server',
    'album.server',
    # static_folder='static',
    # static_url_path='/bokeh/static',
    # template_folder='templates'
)


def object_page(prefix):
    """ Decorator for a function which turns an object into a web page

    from bokeh.server.app import bokeh_app
    @bokeh_app.route("/myapp")
    @object_page("mypage")
    def make_object():
        #make some bokeh object here
        return obj

    This decorator will
      - create a randomized title for a bokeh document using the prefix
      - initialize bokeh plotting libraries to use that document
      - call the function you pass in, add that object to the plot context
      - render that object in a web page

    Note: copied from bokeh.server.utils.plugins:object_page. git describe on
          bokeh was 0.10.0-76-g25cf53d
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            ## setup the randomly titled document
            docname = prefix + str(uuid.uuid4())
            # bokehuser = bokeh_app.current_user()
            bokehuser = 'foo'
            try:
                doc = _makedoc(bokeh_app.servermodel_storage, bokehuser, docname)
                doc.published = True
                doc.save(bokeh_app.servermodel_storage)
            except DataIntegrityException as e:
                return abort(409, e.message)
            docid = doc.docid
            clientdoc = bokeh_app.backbone_storage.get_document(docid)

            ## initialize our plotting APIs to use that document

            init_bokeh(clientdoc)
            obj = func(*args, **kwargs)
            clientdoc.add(obj)
            bokeh_app.backbone_storage.store_document(clientdoc)
            if hasattr(obj, 'extra_generated_classes'):
                extra_generated_classes = obj.extra_generated_classes
            else:
                extra_generated_classes = []

            resources = Resources()
            return render_template("oneobj.html",
                                   elementid=str(uuid.uuid4()),
                                   docid=docid,
                                   objid=obj._id,
                                   hide_navbar=True,
                                   extra_generated_classes=extra_generated_classes,
                                   public='true',
                                   loglevel=resources.log_level)
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator
