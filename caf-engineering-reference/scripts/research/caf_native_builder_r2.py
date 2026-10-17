"""R2 native-block builder: copy source graphical records for every clone.

No CCT acceptance is claimed. The R1 implementation is retained separately.
"""
import copy
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from lxml import etree as E

_spec = importlib.util.spec_from_file_location('tocc_native_r2', Path(__file__).with_name('make_ahu_three_tocc_candidate_r2.py'))
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
N = _base.N
MAIN = _base.MAIN
prop = _base.prop
set_prop = _base.set_prop
nv = _base.new_value
array = _base.array
struct = _base.struct
edge = _base.edge
position = _base.position
metadata = _base.metadata
bare_bytes = _base.bare_bytes
replace_property_bytes = _base.replace_property_bytes
parse = _base.parse


@dataclass(frozen=True)
class Type:
    kind: str
    enum: int | None = None
    count: int = 0
    units: int = 95


FLOAT = Type('float')
BOOL = Type('boolean')
OCC = Type('enum', 345, 4)
ENABLE = Type('enum', 349, 2)
OFFON = Type('enum', None, 2)


@dataclass
class Signal:
    obj: E._Element
    port: int
    type: Type


def typed(o):
    cid = o.get('classid')
    if cid in ['526', '527']:
        units = prop(o, 117)
        return Type('float', units=int(units.text) if units is not None else 95)
    if cid in ['530', '531']:
        return BOOL
    if cid in ['528', '529']:
        en, count = prop(o, 931), prop(o, 74)
        return Type('enum', int(en.text) if en is not None else None, int(count.text) if count is not None else 2)
    raise ValueError((o.get('ref'), cid))


def configure_point(o, type_, port=None, name=None, default=None, publish=None):
    if port is not None:
        set_prop(o, 3365, nv('enum', port, set=509))
    if name is not None:
        set_prop(o, 2390, nv('string', name))
    if type_.kind == 'float':
        set_prop(o, 117, nv('enum', type_.units, set=507))
    elif type_.kind == 'enum':
        set_prop(o, 74, nv('unsignedShort', type_.count))
        if type_.enum is not None:
            set_prop(o, 931, nv('enum', type_.enum, set=802))
        else:
            existing = o.find(f"{N}property[@id='931']")
            if existing is not None:
                o.remove(existing)
        labels = {345: ['Occupied', 'Unoccupied', 'Bypass', 'Standby'],
                  349: ['Shutdown', 'Enable'], 374: ['Normal', 'Alarm'],
                  649: ['Inactive', 'Active']}.get(type_.enum)
        if labels:
            set_prop(o, 110, array('listof', [nv('string', s) for s in labels]))
        else:
            existing = o.find(f"{N}property[@id='110']")
            if existing is not None:
                o.remove(existing)
    if default is not None:
        if type_.kind == 'enum':
            value = nv('enum', int(default), **({'set': type_.enum} if type_.enum is not None else {}))
        elif type_.kind == 'boolean':
            value = nv('boolean', 'true' if default else 'false')
        else:
            value = nv('float', default)
        set_prop(o, 3113, value)
    if publish is not None:
        set_prop(o, 3807, nv('boolean', 'true' if publish else 'false'))


class Library(_base.NativeClones):
    def __init__(self, old):
        super().__init__(old)
        self.next_id = 500000
        self.activities = []
        self.interfaces = []
        self.main_port = 7100
        self.layout_sources = {}
        self.native_layouts = {}
        self.layout_provenance = []
        for parent in old.values():
            blocks, locations = prop(parent, 3375), prop(parent, 3383)
            if blocks is None or locations is None:
                continue
            assert len(blocks) == len(locations)
            for block, location in zip(blocks, locations):
                ref = parent.get('ref') + f".{block.get('id')}_{block.text}"
                assert ref in old
                if ref in self.native_layouts:
                    assert bare_bytes(self.native_layouts[ref]) == bare_bytes(location), ref
                self.native_layouts[ref] = copy.deepcopy(location)

    def clone(self, source, parent):
        obj = super().clone(source, parent)
        self.layout_sources[obj.get('ref')] = source
        return obj

    def layout(self, obj, x, y):
        source = self.layout_sources[obj.get('ref')]
        assert source in self.native_layouts, ('no native graphical record', source)
        result = copy.deepcopy(self.native_layouts[source])
        coordinates = list(result.iter(N + 'float'))
        codes = list(result.iter(N + 'unsignedShort'))
        assert len(coordinates) == 2 and len(codes) == 1
        coordinates[0].text, coordinates[1].text = str(x), str(y)
        self.layout_provenance.append({'ref': obj.get('ref'), 'source_ref': source,
                                       'display_code': int(codes[0].text)})
        return result

    def new_activity(self, name):
        o = copy.deepcopy(self.old[MAIN + '.536_86470'])
        oid = self.allocate()
        ref = MAIN + f'.536_{oid}'
        o.set('ref', ref)
        o.set('objectid', str(oid))
        set_prop(o, 32527, nv('string', ref))
        set_prop(o, 75, nv('BACoid', oid, id=536))
        set_prop(o, 2390, nv('string', name))
        self.new[ref] = o
        self.layout_sources[ref] = MAIN + '.536_86470'
        activity = Activity(self, o, name)
        self.activities.append(activity)
        return activity

    def main_input(self, name, type_, default, description):
        template = MAIN + ('.5_14' if type_.kind == 'boolean' else '.2_12')
        assert type_.kind in ['boolean', 'float']
        o = self.clone(template, MAIN)
        configure_point(o, type_, port=self.main_port, name=name, default=default, publish=True)
        set_prop(o, 3670, nv('enum', 0, set=433))
        self.main_port += 1
        self.interfaces.append({'name': name, 'direction': 'input', 'type': type_.kind,
                                'units_enum': type_.units, 'default': default,
                                'object_ref': o.get('ref'), 'description': description})
        return Signal(o, 663, type_)

    def get_port(self, obj, number):
        children = [c for ref, c in {**self.old, **self.new}.items()
                    if ref.rsplit('.', 1)[0] == obj.get('ref') and prop(c, 3365) is not None
                    and int(prop(c, 3365).text) == number]
        assert len(children) == 1, (obj.get('ref'), number)
        return children[0]

    def existing_signal(self, ref, port):
        o = self.old[ref]
        if o.get('classid') in ['526', '527', '528', '529', '530', '531']:
            type_ = typed(o)
        else:
            type_ = typed(self.get_port(o, port))
        return Signal(o, port, type_)


class Activity:
    INPUT = {'float': MAIN + '.536_86466.2_299800',
             'boolean': MAIN + '.536_81051.5_108877',
             'enum': MAIN + '.536_86470.19_300130'}
    OUTPUT = {'float': MAIN + '.536_86466.2_299840',
              'boolean': MAIN + '.536_81051.5_108893',
              'enum': MAIN + '.536_86470.19_300132'}
    MATH = {'add': MAIN + '.536_83810.561_265194',
            'sub': MAIN + '.536_83759.561_261327',
            'mul': MAIN + '.536_62854.561_160176',
            'div': MAIN + '.536_62854.561_160165',
            'min': MAIN + '.536_62854.561_160161',
            'max': MAIN + '.536_62854.561_160105'}

    def __init__(self, library, obj, name):
        self.lib, self.obj, self.name = library, obj, name
        self.ref = obj.get('ref')
        self.blocks, self.wires, self.inputs, self.outputs = [], [], [], []
        self.operations = []

    def add(self, obj, name=None):
        if name:
            set_prop(obj, 2390, nv('string', name))
        self.blocks.append(obj)
        return obj

    def primitive(self, source, name):
        return self.add(self.lib.clone(source, self.ref), name)

    def wire(self, sig, obj, port):
        assert sig.obj in self.blocks and obj in self.blocks, (self.name, sig.obj.get('ref'), obj.get('ref'))
        self.wires.append([self.blocks.index(sig.obj), sig.port, self.blocks.index(obj), port])

    def bind(self, obj, port, value, type_=None):
        child = self.lib.get_port(obj, port)
        if type_ is not None:
            configure_point(child, type_)
        if isinstance(value, Signal):
            actual = typed(child)
            assert actual.kind == value.type.kind, (self.name, obj.get('ref'), port, actual, value.type)
            if actual.kind == 'enum':
                assert actual.enum == value.type.enum, (actual, value.type)
            self.wire(value, obj, port)
        else:
            configure_point(child, type_ or typed(child), default=value)

    def input(self, name, type_, default=0):
        port = 7000 + len(self.inputs)
        o = self.add(self.lib.clone(self.INPUT[type_.kind], self.ref))
        configure_point(o, type_, port=port, name=name, default=default)
        set_prop(o, 3670, nv('enum', 0, set=433))
        self.inputs.append(o)
        return Signal(o, 663, type_)

    def output(self, name, sig, description='', publish=True):
        port = 8000 + len(self.outputs)
        o = self.add(self.lib.clone(self.OUTPUT[sig.type.kind], self.ref))
        configure_point(o, sig.type, port=port, name=name, default=0, publish=publish)
        set_prop(o, 3670, nv('enum', 0, set=433))
        self.wire(sig, o, 513)
        self.outputs.append(o)
        if publish:
            self.lib.interfaces.append({'name': name, 'direction': 'output', 'type': sig.type.kind,
                                        'enum_set': sig.type.enum, 'units_enum': sig.type.units,
                                        'object_ref': o.get('ref'), 'activity_ref': self.ref,
                                        'port': port, 'description': description})
        return Signal(self.obj, port, sig.type)

    def math(self, op, a, b, name=None):
        o = self.primitive(self.MATH[op], name or op.upper())
        self.bind(o, 7000, a)
        self.bind(o, 7001, b)
        self.operations.append({'ref': o.get('ref'), 'operation': op})
        return Signal(o, 85, FLOAT)

    def logic(self, op, *args, name=None):
        assert args
        if op != 'not' and len(args) == 1:
            return args[0]
        if len(args) > 2:
            result = self.logic(op, args[0], args[1], name=name)
            for arg in args[2:]:
                result = self.logic(op, result, arg, name=name)
            return result
        source = {'and': MAIN + '.536_81051.559_108885',
                  'or': MAIN + '.536_81051.559_108889',
                  'not': MAIN + '.536_62854.559_160144'}[op]
        o = self.primitive(source, name or op.upper())
        self.bind(o, 7000, args[0])
        if op != 'not':
            self.bind(o, 7001, args[1])
        self.operations.append({'ref': o.get('ref'), 'operation': op})
        return Signal(o, 85, BOOL)

    def compare(self, op, a, b, differential=0, name=None):
        o = self.primitive(MAIN + '.536_86466.560_298281', name or op.upper())
        setup, role = {'gt': (0, 29), 'lt': (1, 28), 'lte': (2, 31), 'gte': (3, 32)}[op]
        set_prop(o, 518, nv('enum', setup))
        set_prop(o, 3670, nv('enum', role, set=432))
        self.bind(o, 50083, a)
        self.bind(o, 50084, b)
        self.bind(o, 637, differential)
        self.operations.append({'ref': o.get('ref'), 'operation': op})
        return Signal(o, 85, BOOL)

    def enum_bool(self, sig, values_true, name):
        assert sig.type.kind == 'enum'
        o = self.primitive(MAIN + '.536_86466.543_299716', name)
        ip = self.lib.get_port(o, 7000)
        configure_point(ip, sig.type, default=0)
        rows = []
        for value in range(sig.type.count):
            rule = struct([nv('unsignedByte', value), nv('unsignedShort', 0)])
            rows.append(struct([array('listof', [rule]), nv('unsignedShort', int(value in values_true))]))
        set_prop(o, 3138, array('array', rows))
        self.bind(o, 7000, sig)
        self.operations.append({'ref': o.get('ref'), 'operation': 'enum_to_bool'})
        return Signal(o, 32520, BOOL)

    def select(self, select, false, true, type_=FLOAT, name='SELECT'):
        source = MAIN + ('.536_86466.562_265239' if type_.kind == 'float' else '.536_86466.562_265240')
        assert type_.kind in ['float', 'enum']
        o = self.primitive(source, name)
        for port in [85, 7000, 7001]:
            configure_point(self.lib.get_port(o, port), type_, default=0)
        self.bind(o, 961, select)
        self.bind(o, 7000, false, type_)
        self.bind(o, 7001, true, type_)
        self.operations.append({'ref': o.get('ref'), 'operation': 'select'})
        return Signal(o, 85, type_)

    def reliability(self, sig, name):
        source = {'float': MAIN + '.536_86466.539_298246',
                  'enum': MAIN + '.536_86467.539_298248',
                  'boolean': MAIN + '.536_67893.539_67908'}[sig.type.kind]
        o = self.primitive(source, name)
        configure_point(self.lib.get_port(o, 513), sig.type)
        self.bind(o, 513, sig)
        self.operations.append({'ref': o.get('ref'), 'operation': 'reliable'})
        return Signal(o, 85, BOOL)

    def safe_bool(self, sig, default=False, name='Reliable Boolean'):
        """Select a reliable constant on bad quality, using native selectors.

        The selected input controls MUX reliability; verify this path in CCT.
        """
        encoded = self.select(sig, 0, 1, OFFON, name + ' Encode')
        good = self.reliability(sig, name + ' Quality')
        resolved = self.select(good, int(default), encoded, OFFON, name + ' Fallback')
        return self.enum_bool(resolved, {1}, name)

    def timer(self, input_, duration, reset, setup, name):
        o = self.primitive(MAIN + '.536_86470.558_299720', name)
        configure_point(self.lib.get_port(o, 518), Type('enum', 21, 9), default=setup)
        self.bind(o, 513, input_)
        self.bind(o, 1080, duration)
        self.bind(o, 1082, reset)
        # All these port objects exist in the native subtree. Expose duration,
        # reset, and remaining-time ports for the new connections.
        set_prop(o, 3184, array('array', [nv('enum', i, set=509) for i in [513, 1080, 1082, 85, 1081]]))
        self.operations.append({'ref': o.get('ref'), 'operation': 'timer', 'setup': setup})
        return Signal(o, 85, BOOL), Signal(o, 1081, Type('float', units=73))

    def finish(self):
        set_prop(self.obj, 3375, array('array', [copy.deepcopy(prop(o, 75)) for o in self.blocks]))
        set_prop(self.obj, 3117, array('array', [nv('unsignedShort', i) for i in range(len(self.blocks))]))
        layout = []
        for i, o in enumerate(self.blocks):
            if o in self.inputs:
                x, y = -1600, self.inputs.index(o)*70
            elif o in self.outputs:
                x, y = 3000, self.outputs.index(o)*70
            else:
                j = i - len(self.inputs)
                x, y = -1200 + (j % 8)*480, (j // 8)*120
            layout.append(self.lib.layout(o, x, y))
        set_prop(self.obj, 3383, array('listof', layout))
        set_prop(self.obj, 3118, array('array', [edge(e) for e in self.wires]))
        set_prop(self.obj, 3384, array('listof', [metadata() for _ in self.wires]))
        set_prop(self.obj, 3184, array('array', [nv('enum', prop(o, 3365).text, set=509)
                                               for o in [*self.inputs, *self.outputs]]))
        set_prop(self.obj, 3373, nv('boolean', 'true'))
        return self.obj
