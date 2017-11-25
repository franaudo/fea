"""An example compas_fea package use for beam elements."""

from compas_fea.cad import rhino

from compas_fea.structure import CircularSection
from compas_fea.structure import ElasticIsotropic
from compas_fea.structure import ElementProperties as Properties
from compas_fea.structure import GeneralDisplacement
from compas_fea.structure import GeneralStep
from compas_fea.structure import PointLoad
from compas_fea.structure import Structure

from compas_rhino.utilities import clear_layers

from math import pi

import rhinoscriptsyntax as rs


__author__     = ['Andrew Liew <liew@arch.ethz.ch>']
__copyright__  = 'Copyright 2017, BLOCK Research Group - ETH Zurich'
__license__    = 'MIT License'
__email__      = 'liew@arch.ethz.ch'


rs.EnableRedraw(False)

# Create empty Structure object

mdl = Structure(name='beam_simple', path='C:/Temp/')

# Clear layers

clear_layers(['elset_lines', 'nset_left', 'nset_right', 'nset_weights'])

# Create beam lines

L = 1.0
m = 100
x = [i * L / m for i in range(m + 1)]
rs.CurrentLayer('elset_lines')
[rs.AddLine([x[i], 0, 0], [x[i + 1], 0, 0]) for i in range(m)]

# Create end-points

rs.CurrentLayer('nset_left')
rs.AddPoint([0, 0, 0])
rs.CurrentLayer('nset_right')
rs.AddPoint([L, 0, 0])

# Create weights

spacing = 5
rs.CurrentLayer('nset_weights')
for xi in x[spacing::spacing]:
    rs.AddPoint([xi, 0, 0])

rs.EnableRedraw(True)

# Add beam elements from Network

network = rhino.network_from_lines(layer='elset_lines')
mdl.add_nodes_elements_from_network(network=network, element_type='BeamElement')

# Add node and element sets

rhino.add_sets_from_layers(mdl, layers=['nset_left', 'nset_right', 'nset_weights'])
rhino.add_sets_from_layers(mdl, layers=['elset_lines'], explode=True)

# Add materials

mdl.add_material(ElasticIsotropic(name='mat_elastic', E=20*10**9, v=0.3, p=1500))

# Add sections

_, elements, arcL, L = rhino.ordered_network(mdl, network=network, layer='nset_left')
for c, Li in enumerate(arcL):
    ri = (Li / L) * 0.020 + 0.020
    ele = elements[c]
    sname = 'sec_rod_{0}'.format(ele)
    ename = 'element_{0}'.format(ele)
    mdl.add_section(CircularSection(name=sname, r=ri))
    ep = Properties(material='mat_elastic', section=sname, elsets=ename)
    mdl.add_element_properties(ep, name='ep_{0}'.format(ele))

# Add loads

mdl.add_load(PointLoad(name='load_weights', nodes='nset_weights', z=-1.0))

# Add displacements

deg = pi / 180
mdl.add_displacements([
    GeneralDisplacement(name='disp_left', nodes='nset_left', x=0, y=0, z=0, xx=0, yy=30*deg),
    GeneralDisplacement(name='disp_right', nodes='nset_right', y=0, z=-0.2, zz=0, yy=30*deg)])

# Add steps

mdl.add_steps([
    GeneralStep(name='step_bc', displacements=['disp_left', 'disp_right']),
    GeneralStep(name='step_load', loads=['load_weights'])])
mdl.steps_order = ['step_bc', 'step_load']

# Structure summary

mdl.summary()

# Run and extract data

mdl.analyse_and_extract(software='abaqus', fields=['u', 'ur', 'sf', 'sm'])

# Plot displacements

rhino.plot_data(mdl, step='step_load', field='um', radius=0.01, colorbar_size=0.3)
rhino.plot_data(mdl, step='step_load', field='ury', radius=0.01, colorbar_size=0.3)

# Plot section forces/moments

rhino.plot_data(mdl, step='step_load', field='sfnx', radius=0.01, colorbar_size=0.3)
rhino.plot_data(mdl, step='step_load', field='sfvy', radius=0.01, colorbar_size=0.3)
rhino.plot_data(mdl, step='step_load', field='smy', radius=0.01, colorbar_size=0.3)