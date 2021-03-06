#!/usr/bin/env/python
"""
Pyrate - Optical raytracing based on Python

Copyright (C) 2014-2018
               by     Moritz Esslinger moritz.esslinger@web.de
               and    Johannes Hartung j.hartung@gmx.net
               and    Uwe Lippmann  uwe.lippmann@web.de
               and    Thomas Heinze t.heinze@uni-jena.de
               and    others

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from pyrateoptics.sampling2d import raster
from pyrateoptics.material.material_isotropic import ConstantIndexGlass
from pyrateoptics.material.material_glasscat import refractiveindex_dot_info_glasscatalog, CatalogMaterial
from pyrateoptics.raytracer.surfShape import Asphere
from pyrateoptics.raytracer.optical_element import OpticalElement
from pyrateoptics.raytracer.surface import Surface
from pyrateoptics.raytracer.optical_system import OpticalSystem
from pyrateoptics.raytracer.ray import RayBundle

from pyrateoptics.raytracer.aperture import CircularAperture
from pyrateoptics.raytracer.localcoordinates import LocalCoordinates

from pyrateoptics.raytracer.globalconstants import degree
from pyrateoptics import collimated_bundle, draw

import logging
logging.basicConfig(level=logging.DEBUG)

wavelength = 0.5876e-3

wave_red = 0.700e-3
wave_blue = 0.470e-3




# definition of optical system
s = OpticalSystem() 

dropletradius = 0.1

lc0 = s.addLocalCoordinateSystem(LocalCoordinates(name="stop", decz=0.0), refname=s.rootcoordinatesystem.name)
lccomprism = s.addLocalCoordinateSystem(LocalCoordinates(name="dropletcenter", decz=2.*dropletradius), refname=lc0.name)

lc1 = s.addLocalCoordinateSystem(LocalCoordinates(name="surf1", decz=-dropletradius), refname=lccomprism.name) # objectDist
lc2 = s.addLocalCoordinateSystem(LocalCoordinates(name="surf2", decz=dropletradius), refname=lccomprism.name)
lc3 = s.addLocalCoordinateSystem(LocalCoordinates(name="surf3", decz=0), refname=lccomprism.name)
lc4 = s.addLocalCoordinateSystem(LocalCoordinates(name="image", decz=-2.*dropletradius), refname=lccomprism.name)


stopsurf = Surface(lc0, apert=CircularAperture(lc0, 7*dropletradius))
frontsurf = Surface(lc1, shape=Asphere(lc1, curv=1./dropletradius), apert=CircularAperture(lc1, dropletradius))
rearsurf = Surface(lc2, shape=Asphere(lc2, curv=-1./dropletradius), apert=CircularAperture(lc2, dropletradius))
midsurf = Surface(lc3, shape=Asphere(lc3, curv=0), apert=CircularAperture(lc3, dropletradius))

image = Surface(lc4, apert=CircularAperture(lc4, 7.*dropletradius))


elem = OpticalElement(lc0, name="droplet")



try:
    database_basepath = "refractiveindex.info-database/database"     
    shelf = "3d"
    book  = "liquids"
    page  = "water"    


    gcat = refractiveindex_dot_info_glasscatalog(database_basepath)

    waterdict = gcat.getMaterialDict(shelf, book, page)
    water = CatalogMaterial(lc0, waterdict, name="water (catalogue)")

except:
    logging.warn("refractive index database not found. please download it and symlink\n\
            to it in your local pyrate directory")
    water = ConstantIndexGlass(lc0, n=1.336, name="water (failsafe)")

logging.info("wavelength %f, index %f" % (wave_red, water.getIndex(None, wave_red).real))
logging.info("wavelength %f, index %f" % (wave_blue, water.getIndex(None, wave_blue).real))

elem.addMaterial("water", water)

elem.addSurface("stop", stopsurf, (None, None))
elem.addSurface("surf1", frontsurf, (None, "water"))
elem.addSurface("surf2", rearsurf, ("water", "water"))
elem.addSurface("surf4", frontsurf, ("water", None))
elem.addSurface("image", image, (None, None))

s.addElement("droplet", elem)

sysseq = [("droplet", 
           [
                ("stop", {"is_stop":True}), 
                ("surf1", {}), 
                ("surf2", {"is_mirror":True}),
                ("surf4", {}), 
                ("image", {})])]

(o, k_red, E0_red) = collimated_bundle(11, 
    {"opticalsystem":s, 
     "radius":dropletradius*0.05,
     "starty":dropletradius*0.9,
     "anglex":-12.*degree,
     "raster":raster.MeridionalFan()
     }, wave=wave_red)

(o, k_blue, E0_blue) = collimated_bundle(11, 
    {"opticalsystem":s, 
     "radius":dropletradius*0.05,
     "starty":dropletradius*0.9,
     "anglex":-12.*degree,
     "raster":raster.MeridionalFan()
     }, wave=wave_blue)


initialbundle_red = RayBundle(x0=o, k0=k_red, Efield0=E0_red, wave=wave_red)
initialbundle_blue = RayBundle(x0=o, k0=k_blue, Efield0=E0_blue, wave=wave_blue)
r_red = s.seqtrace(initialbundle_red, sysseq)
r_blue = s.seqtrace(initialbundle_blue, sysseq)

draw(s, [(r_red, "red"), (r_blue, "blue")])

