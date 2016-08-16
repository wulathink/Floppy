# import lauescript
# from lauescript.laueio import loader
from lauescript.cryst.transformations import frac2cart
from lauescript.types.adp import ADPDataError
from floppy.node import Node, abstractNode, Input, Output, Tag
from floppy.FloppyTypes import Atom
import subprocess
import os

@abstractNode
class CrystNode(Node):
    Tag('Crystallography')


class ReadAtoms(CrystNode):
    Input('FileName', str)
    Output('Atoms', Atom, list=True)

    def run(self):
        super(ReadAtoms, self).run()
        from lauescript.laueio.loader import Loader
        loader = Loader()
        loader.create(self._FileName)
        mol = loader.load('quickloadedMolecule')
        self._Atoms(mol.atoms)


class BreakAtom(CrystNode):
    Input('Atom', Atom)
    Output('Name', str)
    Output('Element', str)
    Output('frac', float, list=True)
    Output('cart', float, list=True)
    Output('ADP',float, list=True)
    Output('ADP_Flag', str)
    Output('Cell',float, list=True)

    def run(self):
        super(BreakAtom, self).run()
        atom = self._Atom
        # print(atom, atom.molecule.get_cell(degree=True))
        self._Name(atom.get_name())
        self._Element(atom.get_element())
        self._frac(atom.get_frac())
        self._cart(atom.get_cart())
        try:
            adp = atom.adp['cart_meas']
        except ADPDataError:
            adp = [0, 0, 0, 0, 0, 0]
        self._ADP(adp)
        self._ADP_Flag(atom.adp['flag'])
        self._Cell(atom.molecule.get_cell(degree=True))

    # def check(self):
    #     for inp in self.inputs.values():
    #         print(inp.value)
    #     return super(BreakAtom, self).check()


class Frac2Cart(CrystNode):
    Input('Position', float, list=True)
    Input('Cell', float, list=True)
    Output('Cart', float, list=True)

    def run(self):
        super(Frac2Cart, self).run()
        self._Cart(frac2cart(self._Position, self._Cell))


class SelectAtom(CrystNode):
    Input('AtomList', Atom, list=True)
    Input('AtomName', str)
    Output('Atom', Atom)

    def run(self):
        super(SelectAtom, self).run()
        name = self._AtomName
        self._Atom([atom for atom in self._AtomList if atom.get_name() == name][0])


class PDB2INS(CrystNode):
    Input('FileName', str)
    Input('Wavelength', float)
    Input('HKLF', int)
    Input('CELL', str)
    Input('SpaceGroup', str)
    Input('ANIS', bool)
    Input('MakeHKL', bool)
    Input('REDO', bool)
    Input('Z', int)
    Output('INS', str)
    Output('HKL', str)
    Output('PDB', str)

    def check(self):
        return self.inputs['FileName'].isAvailable()

    def run(self):
        super(PDB2INS, self).run()
        opt =  ('pdb2ins',
                self._FileName,
                '-i',
                '-o __pdb2ins__.ins',
                ' -w '+str(self._Wavelength) if self._Wavelength else '',
                ' -h '+str(self._HKLF) if self._HKLF else '',
                ' -c '+str(self._CELL) if self._CELL else '',
                ' -s '+str(self._SpaceGroup) if self._SpaceGroup else '',
                ' -a ' if self._ANIS else '',
                ' -b ' if self._MakeHKL else '-b',
                ' -r ' if self._REDO else '',
                ' -z ' + str(self._Z) if self._Z else '')
        opt = ' '.join(opt)
        print(opt)
        # opt = [o for o in ' '.join(opt).split(' ') if o]
        # print(opt)
        self.p = subprocess.Popen(opt, shell=True)
        os.waitpid(self.p.pid, 0)
        # print('ran')
        self._INS(open('__pdb2ins__.ins', 'r').read())
        try:
            self._HKL(open('__pdb2ins__.hkl', 'r').read())
        except IOError:
            self._HKL('')
        self._PDB(open('__pdb2ins__.pdb', 'r').read())

