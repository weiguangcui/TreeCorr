# Copyright (c) 2003-2015 by Mike Jarvis
#
# TreeCorr is free software: redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions, and the disclaimer given in the accompanying LICENSE
#    file.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions, and the disclaimer given in the documentation
#    and/or other materials provided with the distribution.

from __future__ import print_function
import numpy
import treecorr
import os
import fitsio

from test_helper import get_from_wiki, get_script_name
from numpy import sin, cos, tan, arcsin, arccos, arctan, arctan2, pi

def test_gg():
    # cf. http://adsabs.harvard.edu/abs/2002A%26A...389..729S for the basic formulae I use here.
    #
    # Use gamma_t(r) = gamma0 r^2/r0^2 exp(-r^2/2r0^2)
    # i.e. gamma(r) = -gamma0 exp(-r^2/2r0^2) (x+iy)^2 / r0^2
    #
    # The Fourier transform is: gamma~(k) = -2 pi gamma0 r0^4 k^2 exp(-r0^2 k^2/2) / L^2
    # P(k) = (1/2pi) <|gamma~(k)|^2> = 2 pi gamma0^2 r0^8 k^4 / L^4 exp(-r0^2 k^2)
    # xi+(r) = (1/2pi) int( dk k P(k) J0(kr) ) 
    #        = pi/16 gamma0^2 (r0/L)^2 exp(-r^2/4r0^2) (r^4 - 16r^2r0^2 + 32r0^4)/r0^4
    # xi-(r) = (1/2pi) int( dk k P(k) J4(kr) ) 
    #        = pi/16 gamma0^2 (r0/L)^2 exp(-r^2/4r0^2) r^4/r0^4
    # Note: I'm not sure I handled the L factors correctly, but the units at the end need
    # to be gamma^2, so it needs to be (r0/L)^2. 

    gamma0 = 0.05
    r0 = 10.
    if __name__ == "__main__":
        ngal = 1000000
        L = 50.*r0  # Not infinity, so this introduces some error.  Our integrals were to infinity.
        req_factor = 1
    else:
        ngal = 200000
        L = 50.*r0
        req_factor = 3
    numpy.random.seed(8675309)
    x = (numpy.random.random_sample(ngal)-0.5) * L
    y = (numpy.random.random_sample(ngal)-0.5) * L
    r2 = (x**2 + y**2)/r0**2
    g1 = -gamma0 * numpy.exp(-r2/2.) * (x**2-y**2)/r0**2
    g2 = -gamma0 * numpy.exp(-r2/2.) * (2.*x*y)/r0**2

    cat = treecorr.Catalog(x=x, y=y, g1=g1, g2=g2, x_units='arcmin', y_units='arcmin')
    gg = treecorr.GGCorrelation(bin_size=0.1, min_sep=1., max_sep=100., sep_units='arcmin',
                                verbose=1)
    gg.process(cat)

    # log(<R>) != <logR>, but it should be close:
    print('meanlogr - log(meanr) = ',gg.meanlogr - numpy.log(gg.meanr))
    numpy.testing.assert_almost_equal(gg.meanlogr, numpy.log(gg.meanr), decimal=3)

    r = gg.meanr
    temp = numpy.pi/16. * gamma0**2 * (r0/L)**2 * numpy.exp(-0.25*r**2/r0**2)
    true_xip = temp * (r**4 - 16.*r**2*r0**2 + 32.*r0**4)/r0**4
    true_xim = temp * r**4/r0**4

    print('gg.xip = ',gg.xip)
    print('true_xip = ',true_xip)
    print('ratio = ',gg.xip / true_xip)
    print('diff = ',gg.xip - true_xip)
    print('max diff = ',max(abs(gg.xip - true_xip)))
    assert max(abs(gg.xip - true_xip))/req_factor < 3.e-7
    print('xip_im = ',gg.xip_im)
    assert max(abs(gg.xip_im))/req_factor < 2.e-7

    print('gg.xim = ',gg.xim)
    print('true_xim = ',true_xim)
    print('ratio = ',gg.xim / true_xim)
    print('diff = ',gg.xim - true_xim)
    print('max diff = ',max(abs(gg.xim - true_xim)))
    assert max(abs(gg.xim - true_xim))/req_factor < 3.e-7
    print('xim_im = ',gg.xim_im)
    assert max(abs(gg.xim_im))/req_factor < 1.e-7

    # Should also work as a cross-correlation with itself
    gg.process(cat,cat)
    numpy.testing.assert_almost_equal(gg.meanlogr, numpy.log(gg.meanr), decimal=3)
    assert max(abs(gg.xip - true_xip))/req_factor < 3.e-7
    assert max(abs(gg.xip_im))/req_factor < 2.e-7
    assert max(abs(gg.xim - true_xim))/req_factor < 3.e-7
    assert max(abs(gg.xim_im))/req_factor < 1.e-7

    # Check MapSq calculation:
    # cf. http://adsabs.harvard.edu/abs/2004MNRAS.352..338J
    # Use Crittenden formulation, since the analytic result is simpler:
    # Map^2(R) = int 1/2 r/R^2 (T+(r/R) xi+(r) + T-(r/R) xi-(r)) dr
    #          = 6 pi gamma0^2 r0^8 R^4 / (L^2 (r0^2+R^2)^5)
    # Mx^2(R)  = int 1/2 r/R^2 (T+(r/R) xi+(r) - T-(r/R) xi-(r)) dr
    #          = 0
    # where T+(s) = (s^4-16s^2+32)/128 exp(-s^2/4)
    #       T-(s) = s^4/128 exp(-s^2/4)
    true_mapsq = 6.*numpy.pi * gamma0**2 * r0**8 * r**4 / (L**2 * (r**2+r0**2)**5)

    mapsq, mapsq_im, mxsq, mxsq_im, varmapsq = gg.calculateMapSq('Crittenden')
    print('mapsq = ',mapsq)
    print('true_mapsq = ',true_mapsq)
    print('ratio = ',mapsq/true_mapsq)
    print('diff = ',mapsq-true_mapsq)
    print('max diff = ',max(abs(mapsq - true_mapsq)))
    print('max diff[16:] = ',max(abs(mapsq[16:] - true_mapsq[16:])))
    # It's pretty ratty near the start where the integral is poorly evaluated, but the 
    # agreement is pretty good if we skip the first 16 elements.
    # Well, it gets bad again at the end, but those values are small enough that they still
    # pass this test.
    assert max(abs(mapsq[16:]-true_mapsq[16:]))/req_factor < 3.e-8
    print('mxsq = ',mxsq)
    print('max = ',max(abs(mxsq)))
    print('max[16:] = ',max(abs(mxsq[16:])))
    assert max(abs(mxsq[16:]))/req_factor < 3.e-8

    # Check that we get the same result using the corr2 executable:
    if __name__ == '__main__':
        cat.write(os.path.join('data','gg.dat'))
        import subprocess
        corr2_exe = get_script_name('corr2')
        p = subprocess.Popen( [corr2_exe,"gg.yaml"] )
        p.communicate()
        corr2_output = numpy.genfromtxt(os.path.join('output','gg.out'), names=True)
        print('gg.xip = ',gg.xip)
        print('from corr2 output = ',corr2_output['xip'])
        print('ratio = ',corr2_output['xip']/gg.xip)
        print('diff = ',corr2_output['xip']-gg.xip)
        numpy.testing.assert_almost_equal(corr2_output['xip']/gg.xip, 1., decimal=3)

        print('gg.xim = ',gg.xim)
        print('from corr2 output = ',corr2_output['xim'])
        print('ratio = ',corr2_output['xim']/gg.xim)
        print('diff = ',corr2_output['xim']-gg.xim)
        numpy.testing.assert_almost_equal(corr2_output['xim']/gg.xim, 1., decimal=3)

        print('xip_im from corr2 output = ',corr2_output['xip_im'])
        print('max err = ',max(abs(corr2_output['xip_im'])))
        assert max(abs(corr2_output['xip_im']))/req_factor < 2.e-7
        print('xim_im from corr2 output = ',corr2_output['xim_im'])
        print('max err = ',max(abs(corr2_output['xim_im'])))
        assert max(abs(corr2_output['xim_im']))/req_factor < 1.e-7

        corr2_output2 = numpy.genfromtxt(os.path.join('output','gg_m2.out'), names=True)
        print('mapsq = ',mapsq)
        print('from corr2 output = ',corr2_output2['Mapsq'])
        print('ratio = ',corr2_output2['Mapsq']/mapsq)
        print('diff = ',corr2_output2['Mapsq']-mapsq)
        numpy.testing.assert_almost_equal(corr2_output2['Mapsq']/mapsq, 1., decimal=3)

        print('mxsq = ',mxsq)
        print('from corr2 output = ',corr2_output2['Mxsq'])
        print('ratio = ',corr2_output2['Mxsq']/mxsq)
        print('diff = ',corr2_output2['Mxsq']-mxsq)
        numpy.testing.assert_almost_equal(corr2_output2['Mxsq']/mxsq, 1., decimal=3)

    # Check the fits write option
    out_file_name = os.path.join('output','gg_out.fits')
    gg.write(out_file_name)
    data = fitsio.read(out_file_name)
    numpy.testing.assert_almost_equal(data['R_nom'], numpy.exp(gg.logr))
    numpy.testing.assert_almost_equal(data['meanR'], gg.meanr)
    numpy.testing.assert_almost_equal(data['meanlogR'], gg.meanlogr)
    numpy.testing.assert_almost_equal(data['xip'], gg.xip)
    numpy.testing.assert_almost_equal(data['xim'], gg.xim)
    numpy.testing.assert_almost_equal(data['xip_im'], gg.xip_im)
    numpy.testing.assert_almost_equal(data['xim_im'], gg.xim_im)
    numpy.testing.assert_almost_equal(data['sigma_xi'], numpy.sqrt(gg.varxi))
    numpy.testing.assert_almost_equal(data['weight'], gg.weight)
    numpy.testing.assert_almost_equal(data['npairs'], gg.npairs)

    # Check the read function
    gg2 = treecorr.GGCorrelation(bin_size=0.1, min_sep=1., max_sep=100., sep_units='arcmin')
    gg2.read(out_file_name)
    numpy.testing.assert_almost_equal(gg2.logr, gg.logr)
    numpy.testing.assert_almost_equal(gg2.meanr, gg.meanr)
    numpy.testing.assert_almost_equal(gg2.meanlogr, gg.meanlogr)
    numpy.testing.assert_almost_equal(gg2.xip, gg.xip)
    numpy.testing.assert_almost_equal(gg2.xim, gg.xim)
    numpy.testing.assert_almost_equal(gg2.xip_im, gg.xip_im)
    numpy.testing.assert_almost_equal(gg2.xim_im, gg.xim_im)
    numpy.testing.assert_almost_equal(gg2.varxi, gg.varxi)
    numpy.testing.assert_almost_equal(gg2.weight, gg.weight)
    numpy.testing.assert_almost_equal(gg2.npairs, gg.npairs)

    # Also check the Schneider version.  The math isn't quite as nice here, but it is tractable
    # using a different formula than I used above:
    # Map^2(R) = int k P(k) W(kR) dk
    #          = 576 pi gamma0^2 r0^6/(L^2 R^4) exp(-R^2/2r0^2) (I4(R^2/2r0^2)
    # where I4 is the modified Bessel function with nu=4.
    try:
        from scipy.special import iv
        x = 0.5*r**2/r0**2
        true_mapsq = 144.*numpy.pi * gamma0**2 * r0**2 / (L**2 * x**2) * numpy.exp(-x) * iv(4,x)

        mapsq, mapsq_im, mxsq, mxsq_im, varmapsq = gg.calculateMapSq('Schneider')
        print('Schneider mapsq = ',mapsq)
        print('true_mapsq = ',true_mapsq)
        print('ratio = ',mapsq/true_mapsq)
        print('diff = ',mapsq-true_mapsq)
        print('max diff = ',max(abs(mapsq - true_mapsq)))
        print('max diff[20:] = ',max(abs(mapsq[20:] - true_mapsq[20:])))
        # This one stays ratty longer, so we need to skip the first 20 and also loosen the
        # test a bit.
        assert max(abs(mapsq[20:]-true_mapsq[20:])) < 7.e-8
        print('mxsq = ',mxsq)
        print('max = ',max(abs(mxsq)))
        print('max[20:] = ',max(abs(mxsq[20:])))
        assert max(abs(mxsq[20:])) < 7.e-8

    except ImportError:
        # Don't require scipy if the user doesn't have it.
        print('Skipping tests of Schneider aperture mass, since scipy.special not available.')


def test_spherical():
    # This is the same field we used for test_gg, but put into spherical coords.
    # We do the spherical trig by hand using the obvious formulae, rather than the clever
    # optimizations that are used by the TreeCorr code, thus serving as a useful test of
    # the latter.

    gamma0 = 0.05
    r0 = 10. * treecorr.arcmin
    if __name__ == "__main__":
        nsource = 1000000
        L = 50.*r0  # Not infinity, so this introduces some error.  Our integrals were to infinity.
        req_factor = 1
    else:
        nsource = 200000
        L = 50.*r0
        req_factor = 3
    numpy.random.seed(8675309)
    x = (numpy.random.random_sample(nsource)-0.5) * L
    y = (numpy.random.random_sample(nsource)-0.5) * L
    r2 = x**2 + y**2
    g1 = -gamma0 * numpy.exp(-r2/2./r0**2) * (x**2-y**2)/r0**2
    g2 = -gamma0 * numpy.exp(-r2/2./r0**2) * (2.*x*y)/r0**2
    r = numpy.sqrt(r2)
    theta = arctan2(y,x)

    gg = treecorr.GGCorrelation(bin_size=0.1, min_sep=1., max_sep=100., sep_units='arcmin',
                                verbose=1)
    r1 = numpy.exp(gg.logr) * treecorr.arcmin
    temp = numpy.pi/16. * gamma0**2 * (r0/L)**2 * numpy.exp(-0.25*r1**2/r0**2)
    true_xip = temp * (r1**4 - 16.*r1**2*r0**2 + 32.*r0**4)/r0**4
    true_xim = temp * r1**4/r0**4

    # Test this around several central points
    if __name__ == '__main__':
        ra0_list = [ 0., 1., 1.3, 232., 0. ]
        dec0_list = [ 0., -0.3, 1.3, -1.4, pi/2.-1.e-6 ]
    else:
        ra0_list = [ 232.]
        dec0_list = [ -1.4 ]

    for ra0, dec0 in zip(ra0_list, dec0_list):

        # Use spherical triangle with A = point, B = (ra0,dec0), C = N. pole
        # a = Pi/2-dec0
        # c = 2*asin(r/2)  (lambert projection)
        # B = Pi/2 - theta

        c = 2.*arcsin(r/2.)
        a = pi/2. - dec0
        B = pi/2. - theta
        B[x<0] *= -1.
        B[B<-pi] += 2.*pi
        B[B>pi] -= 2.*pi

        # Solve the rest of the triangle with spherical trig:
        cosb = cos(a)*cos(c) + sin(a)*sin(c)*cos(B)
        b = arccos(cosb)
        cosA = (cos(a) - cos(b)*cos(c)) / (sin(b)*sin(c))
        #A = arccos(cosA)
        A = numpy.zeros_like(cosA)
        A[abs(cosA)<1] = arccos(cosA[abs(cosA)<1])
        A[cosA<=-1] = pi
        cosC = (cos(c) - cos(a)*cos(b)) / (sin(a)*sin(b))
        #C = arccos(cosC)
        C = numpy.zeros_like(cosC)
        C[abs(cosC)<1] = arccos(cosC[abs(cosC)<1])
        C[cosC<=-1] = pi
        C[x<0] *= -1.

        ra = ra0 - C
        dec = pi/2. - b

        # Rotate shear relative to local west
        # gamma_sph = exp(2i beta) * gamma
        # where beta = pi - (A+B) is the angle between north and "up" in the tangent plane.
        beta = pi - (A+B)
        beta[x>0] *= -1.
        cos2beta = cos(2.*beta)
        sin2beta = sin(2.*beta)
        g1_sph = g1 * cos2beta - g2 * sin2beta
        g2_sph = g2 * cos2beta + g1 * sin2beta

        cat = treecorr.Catalog(ra=ra, dec=dec, g1=g1_sph, g2=g2_sph, ra_units='rad', 
                               dec_units='rad')
        gg = treecorr.GGCorrelation(bin_size=0.1, min_sep=1., max_sep=100., sep_units='arcmin',
                                    verbose=1)
        gg.process(cat)

        print('ra0, dec0 = ',ra0,dec0)
        print('gg.xip = ',gg.xip)
        print('true_xip = ',true_xip)
        print('ratio = ',gg.xip / true_xip)
        print('diff = ',gg.xip - true_xip)
        print('max diff = ',max(abs(gg.xip - true_xip)))
        # The 3rd and 4th centers are somewhat less accurate.  Not sure why.
        # The math seems to be right, since the last one that gets all the way to the pole
        # works, so I'm not sure what is going on.  It's just a few bins that get a bit less
        # accurate.  Possibly worth investigating further at some point...
        assert max(abs(gg.xip - true_xip))/req_factor < 3.e-7

        print('gg.xim = ',gg.xim)
        print('true_xim = ',true_xim)
        print('ratio = ',gg.xim / true_xim)
        print('diff = ',gg.xim - true_xim)
        print('max diff = ',max(abs(gg.xim - true_xim)))
        assert max(abs(gg.xim - true_xim))/req_factor < 2.e-7

    # One more center that can be done very easily.  If the center is the north pole, then all
    # the tangential shears are pure (positive) g1.
    ra0 = 0
    dec0 = pi/2.
    ra = theta
    dec = pi/2. - 2.*arcsin(r/2.)
    gammat = -gamma0 * r2/r0**2 * numpy.exp(-r2/2./r0**2)

    cat = treecorr.Catalog(ra=ra, dec=dec, g1=gammat, g2=numpy.zeros_like(gammat), ra_units='rad',
                           dec_units='rad')
    gg.process(cat)

    print('gg.xip = ',gg.xip)
    print('gg.xip_im = ',gg.xip_im)
    print('true_xip = ',true_xip)
    print('ratio = ',gg.xip / true_xip)
    print('diff = ',gg.xip - true_xip)
    print('max diff = ',max(abs(gg.xip - true_xip)))
    assert max(abs(gg.xip - true_xip))/req_factor < 3.e-7
    assert max(abs(gg.xip_im))/req_factor < 3.e-7

    print('gg.xim = ',gg.xim)
    print('gg.xim_im = ',gg.xim_im)
    print('true_xim = ',true_xim)
    print('ratio = ',gg.xim / true_xim)
    print('diff = ',gg.xim - true_xim)
    print('max diff = ',max(abs(gg.xim - true_xim)))
    assert max(abs(gg.xim - true_xim))/req_factor < 2.e-7
    assert max(abs(gg.xim_im))/req_factor < 2.e-7

    # Check that we get the same result using the corr2 executable:
    if __name__ == '__main__':
        cat.write(os.path.join('data','gg_spherical.dat'))
        import subprocess
        corr2_exe = get_script_name('corr2')
        p = subprocess.Popen( [corr2_exe,"gg_spherical.yaml"] )
        p.communicate()
        corr2_output = numpy.genfromtxt(os.path.join('output','gg_spherical.out'), names=True)
        print('gg.xip = ',gg.xip)
        print('from corr2 output = ',corr2_output['xip'])
        print('ratio = ',corr2_output['xip']/gg.xip)
        print('diff = ',corr2_output['xip']-gg.xip)
        numpy.testing.assert_almost_equal(corr2_output['xip']/gg.xip, 1., decimal=3)

        print('gg.xim = ',gg.xim)
        print('from corr2 output = ',corr2_output['xim'])
        print('ratio = ',corr2_output['xim']/gg.xim)
        print('diff = ',corr2_output['xim']-gg.xim)
        numpy.testing.assert_almost_equal(corr2_output['xim']/gg.xim, 1., decimal=3)

        print('xip_im from corr2 output = ',corr2_output['xip_im'])
        assert max(abs(corr2_output['xip_im']))/req_factor < 3.e-7

        print('xim_im from corr2 output = ',corr2_output['xim_im'])
        assert max(abs(corr2_output['xim_im']))/req_factor < 2.e-7


def test_aardvark():

    # Eric Suchyta did a brute force calculation of the Aardvark catalog, so it is useful to
    # compare the output from my code with that.

    get_from_wiki('Aardvark.fit')
    file_name = os.path.join('data','Aardvark.fit')
    config = treecorr.read_config('Aardvark.yaml')
    cat1 = treecorr.Catalog(file_name, config)
    gg = treecorr.GGCorrelation(config)
    gg.process(cat1)

    direct_file_name = os.path.join('data','Aardvark.direct')
    direct_data = numpy.genfromtxt(direct_file_name)
    direct_xip = direct_data[:,3]
    direct_xim = direct_data[:,4]

    #print('gg.xip = ',gg.xip)
    #print('direct.xip = ',direct_xip)

    xip_err = gg.xip - direct_xip
    print('xip_err = ',xip_err)
    print('max = ',max(abs(xip_err)))
    assert max(abs(xip_err)) < 2.e-7
    print('xip_im = ',gg.xip_im)
    print('max = ',max(abs(gg.xip_im)))
    assert max(abs(gg.xip_im)) < 3.e-7

    xim_err = gg.xim - direct_xim
    print('xim_err = ',xim_err)
    print('max = ',max(abs(xim_err)))
    assert max(abs(xim_err)) < 1.e-7
    print('xim_im = ',gg.xim_im)
    print('max = ',max(abs(gg.xim_im)))
    assert max(abs(gg.xim_im)) < 1.e-7

    # However, after some back and forth about the calculation, we concluded that Eric hadn't
    # done the spherical trig correctly to get the shears relative to the great circle joining
    # the two positions.  So let's compare with my own brute force calculation (i.e. using
    # bin_slop = 0):
    # This also has the advantage that the radial bins are done the same way -- uniformly 
    # spaced in log of the chord distance, rather than the great circle distance.

    bs0_file_name = os.path.join('data','Aardvark.bs0')
    bs0_data = numpy.genfromtxt(bs0_file_name)
    bs0_xip = bs0_data[:,2]
    bs0_xim = bs0_data[:,3]

    #print('gg.xip = ',gg.xip)
    #print('bs0.xip = ',bs0_xip)

    xip_err = gg.xip - bs0_xip
    print('xip_err = ',xip_err)
    print('max = ',max(abs(xip_err)))
    assert max(abs(xip_err)) < 1.e-7

    xim_err = gg.xim - bs0_xim
    print('xim_err = ',xim_err)
    print('max = ',max(abs(xim_err)))
    assert max(abs(xim_err)) < 5.e-8

    # Check that we get the same result using the corr2 executable:
    # Note: This is the only test of the corr2 executable that we do with nosetests.
    # The other similar tests are blocked out with: if __name__ == '__main__':
    import subprocess
    corr2_exe = get_script_name('corr2')
    p = subprocess.Popen( [corr2_exe,"Aardvark.yaml"] )
    p.communicate()
    corr2_output = numpy.genfromtxt(os.path.join('output','Aardvark.out'), names=True)
    print('gg.xip = ',gg.xip)
    print('from corr2 output = ',corr2_output['xip'])
    print('ratio = ',corr2_output['xip']/gg.xip)
    print('diff = ',corr2_output['xip']-gg.xip)
    numpy.testing.assert_almost_equal(corr2_output['xip']/gg.xip, 1., decimal=3)

    print('gg.xim = ',gg.xim)
    print('from corr2 output = ',corr2_output['xim'])
    print('ratio = ',corr2_output['xim']/gg.xim)
    print('diff = ',corr2_output['xim']-gg.xim)
    numpy.testing.assert_almost_equal(corr2_output['xim']/gg.xim, 1., decimal=3)

    print('xip_im from corr2 output = ',corr2_output['xip_im'])
    print('max err = ',max(abs(corr2_output['xip_im'])))
    assert max(abs(corr2_output['xip_im'])) < 3.e-7
    print('xim_im from corr2 output = ',corr2_output['xim_im'])
    print('max err = ',max(abs(corr2_output['xim_im'])))
    assert max(abs(corr2_output['xim_im'])) < 1.e-7

    # As bin_slop decreases, the agreement should get even better.
    # This test is slow, so only do it if running test_gg.py directly.
    if __name__ == '__main__':
        config['bin_slop'] = 0.2
        gg = treecorr.GGCorrelation(config)
        gg.process(cat1)

        #print('gg.xip = ',gg.xip)
        #print('bs0.xip = ',bs0_xip)

        xip_err = gg.xip - bs0_xip
        print('xip_err = ',xip_err)
        print('max = ',max(abs(xip_err)))
        assert max(abs(xip_err)) < 1.e-8

        xim_err = gg.xim - bs0_xim
        print('xim_err = ',xim_err)
        print('max = ',max(abs(xim_err)))
        assert max(abs(xim_err)) < 1.e-8

 
def test_shuffle():
    # Check that the code is insensitive to shuffling the input data vectors.

    # Might as well use the same function as above, although I reduce L a bit.
    ngal = 10000
    gamma0 = 0.05
    r0 = 10.
    L = 5. * r0
    numpy.random.seed(8675309)
    x = (numpy.random.random_sample(ngal)-0.5) * L
    y = (numpy.random.random_sample(ngal)-0.5) * L
    r2 = (x**2 + y**2)/r0**2
    g1 = -gamma0 * numpy.exp(-r2/2.) * (x**2-y**2)/r0**2
    g2 = -gamma0 * numpy.exp(-r2/2.) * (2.*x*y)/r0**2

    cat_u = treecorr.Catalog(x=x, y=y, g1=g1, g2=g2)
    gg_u = treecorr.GGCorrelation(bin_size=0.1, min_sep=1., max_sep=30., verbose=1)
    gg_u.process(cat_u)

    # Put these in a single 2d array so we can easily use numpy.random.shuffle
    data = numpy.array( [x, y, g1, g2] ).T
    print('data = ',data)
    numpy.random.shuffle(data)

    cat_s = treecorr.Catalog(x=data[:,0], y=data[:,1], g1=data[:,2], g2=data[:,3])
    gg_s = treecorr.GGCorrelation(bin_size=0.1, min_sep=1., max_sep=30., verbose=1)
    gg_s.process(cat_s)

    print('gg_u.xip = ',gg_u.xip)
    print('gg_s.xip = ',gg_s.xip)
    print('ratio = ',gg_u.xip / gg_s.xip)
    print('diff = ',gg_u.xip - gg_s.xip)
    print('max diff = ',max(abs(gg_u.xip - gg_s.xip)))
    assert max(abs(gg_u.xip - gg_s.xip)) < 1.e-14

def test_haloellip():
    """Test that the constant and quadrupole versions of the Clampitt halo ellipticity calculation
    are equivalent to xi+ and xi- (respectively) of the shear-shear cross correlation, where
    the halo ellipticities are normalized to |g_lens|=1.

    Joseph's original formulation: (cf. Issue #36, although I correct what I believe is an error
    in his gamma_Qx formula.)

    gamma_Q = Sum_i (w_i * g1_i * cos(4theta) + w_i * g2_i * sin(4theta)) / Sum_i (w_i)
    gamma_C = Sum_i (w_i * g1_i) / Sum_i (w_i)

    gamma_Qx = Sum_i (w_i * g2_i * cos(4theta) - w_i * g1_i * sin(4theta)) / Sum_i (w_i)
    gamma_Cx = Sum_i (w_i * g2_i) / Sum_i (w_i)

    where g1,g2 and theta are measured w.r.t. the coordinate system where the halo ellitpicity
    is along the x-axis.  Converting this to complex notation, we obtain:

    gamma_C + i gamma_Cx = < g1 + i g2 >
                         = < gobs exp(-2iphi) >
                         = < gobs elens* >
    gamma_Q + i gamma_Qx = < (g1 + i g2) (cos(4t) - isin(4t) >
                         = < gobs exp(-2iphi) exp(-4itheta) >
                         = < gobs exp(2iphi) exp(-4i(theta+phi)) >
                         = < gobs elens exp(-4i(theta+phi)) >

    where gobs is the observed shape of the source in the normal world coordinate system, and
    elens = exp(2iphi) is the unit-normalized shape of the lens in that same coordinate system.
    Note that the combination theta+phi is the angle between the line joining the two points
    and the E-W coordinate, which means that

    gamma_C + i gamma_Cx = xi+(gobs, elens)
    gamma_Q + i gamma_Qx = xi-(gobs, elens)

    We test this result here using the above formulation with both unit weights and weights
    proportional to the halo ellitpicity.  We also try keeping the magnitude of elens rather
    than normalizing it.
    """

    nlens = 1000
    nsource = 10000  # sources per lens
    ntot = nsource * nlens
    L = 100000.  # The side length in which the lenses are placed
    R = 10.      # The (rms) radius of the associated sources from the lenses
                 # In this case, we want L >> R so that most sources are only associated
                 # with the one lens we used for assigning its shear value.

    # Lenses are randomly located with random shapes.
    numpy.random.seed(8675309)
    lens_g1 = numpy.random.normal(0., 0.1, (nlens,))
    lens_g2 = numpy.random.normal(0., 0.1, (nlens,))
    lens_g = lens_g1 + 1j * lens_g2
    lens_absg = numpy.abs(lens_g)
    lens_x = (numpy.random.random_sample(nlens)-0.5) * L
    lens_y = (numpy.random.random_sample(nlens)-0.5) * L
    print('Made lenses')

    e_a = 0.17  # The amplitude of the constant part of the signal
    e_b = 0.23  # The amplitude of the quadrupole part of the signal
    source_g1 = numpy.empty(ntot)
    source_g2 = numpy.empty(ntot)
    source_x = numpy.empty(ntot)
    source_y = numpy.empty(ntot)
    # For the sources, place 100 galaxies around each lens with the expected azimuthal pattern
    # I just use a constant |g| for the amplitude, not a real radial pattern.
    for i in range(nlens):
        # First build the signal as it appears in the coordinate system where the halo
        # is oriented along the x-axis
        dx = numpy.random.normal(0., 10., (nsource,))
        dy = numpy.random.normal(0., 10., (nsource,))
        z = dx + 1j * dy
        exp2iphi = z**2 / numpy.abs(z)**2
        source_g = e_a + e_b * exp2iphi**2
        # Now rotate the whole system by the phase of the lens ellipticity.
        exp2ialpha = lens_g[i] / lens_absg[i]
        expialpha = numpy.sqrt(exp2ialpha)
        source_g *= exp2ialpha
        z *= expialpha
        # Also scale the signal by |lens_g|
        source_g *= lens_absg[i]
        # Place the source galaxies at this dx,dy with this shape
        source_x[i*nsource: (i+1)*nsource] = lens_x[i] + z.real
        source_y[i*nsource: (i+1)*nsource] = lens_y[i] + z.imag
        source_g1[i*nsource: (i+1)*nsource] = source_g.real
        source_g2[i*nsource: (i+1)*nsource] = source_g.imag
    print('Made sources')

    source_cat = treecorr.Catalog(x=source_x, y=source_y, g1=source_g1, g2=source_g2)
    gg = treecorr.GGCorrelation(min_sep=1, max_sep=30, bin_size=0.1)
    lens_mean_absg = numpy.mean(lens_absg)
    print('mean_absg = ',lens_mean_absg)

    # First the original version where we only use the phase of the lens ellipticities:
    lens_absg = numpy.sqrt(lens_g1**2 + lens_g2**2)
    lens_cat1 = treecorr.Catalog(x=lens_x, y=lens_y, g1=lens_g1/lens_absg, g2=lens_g2/lens_absg)
    gg.process(lens_cat1, source_cat)
    print('gg.xim = ',gg.xim)
    # The net signal here is just <absg> * e_b
    print('expected signal = ',e_b * lens_mean_absg)
    # These tests don't quite work at the 1% level of accuracy, but 2% seems to work for most.
    # This is effected by checking that 1/2 the value matches 0.5 to 2 decimal places.
    numpy.testing.assert_almost_equal(gg.xim/(e_b * lens_mean_absg)/2., 0.5, decimal=2)
    print('gg.xip = ',gg.xip)
    print('expected signal = ',e_a * lens_mean_absg)
    numpy.testing.assert_almost_equal(gg.xip/(e_a * lens_mean_absg)/2, 0.5, decimal=2)

    # Next weight the lenses by their absg.
    lens_cat2 = treecorr.Catalog(x=lens_x, y=lens_y, g1=lens_g1/lens_absg, g2=lens_g2/lens_absg,
                                w=lens_absg)
    gg.process(lens_cat2, source_cat)
    print('gg.xim = ',gg.xim)
    # Now the net signal is 
    # sum(w * e_b*absg[i]) / sum(w) 
    # = sum(absg[i]^2 * e_b) / sum(absg[i])
    # = <absg^2> * e_b / <absg>
    lens_mean_gsq = numpy.mean(lens_absg**2)
    print('expected signal = ',e_b * lens_mean_gsq / lens_mean_absg)
    numpy.testing.assert_almost_equal(gg.xim/(e_b * lens_mean_gsq / lens_mean_absg)/2., 0.5,
                                      decimal=2)
    print('gg.xip = ',gg.xip)
    print('expected signal = ',e_a * lens_mean_gsq / lens_mean_absg)
    numpy.testing.assert_almost_equal(gg.xip/(e_a * lens_mean_gsq / lens_mean_absg)/2., 0.5,
                                      decimal=2)

    # Finally, use the unnormalized lens_g for the lens ellipticities
    lens_cat3 = treecorr.Catalog(x=lens_x, y=lens_y, g1=lens_g1, g2=lens_g2)
    gg.process(lens_cat3, source_cat)
    print('gg.xim = ',gg.xim)
    # Now the net signal is 
    # sum(absg[i] * e_b*absg[i]) / N
    # = sum(absg[i]^2 * e_b) / N
    # = <absg^2> * e_b
    print('expected signal = ',e_b * lens_mean_gsq)
    # This one is slightly less accurate.  But easily passes at 3% accuracy.
    numpy.testing.assert_almost_equal(gg.xim/(e_b * lens_mean_gsq)/3., 0.333, decimal=2)
    print('gg.xip = ',gg.xip)
    print('expected signal = ',e_a * lens_mean_gsq)
    numpy.testing.assert_almost_equal(gg.xip/(e_a * lens_mean_gsq)/2., 0.5, decimal=2)

    # It's worth noting that exactly half the signal is in each of g1, g2, so for things
    # like SDSS, you can use only g2, for instance, which avoids some insidious systematic
    # errors related to the scan direction.
    source_cat2 = treecorr.Catalog(x=source_x, y=source_y,
                                   g1=numpy.zeros_like(source_g2), g2=source_g2)
    gg.process(lens_cat1, source_cat2)
    print('gg.xim = ',gg.xim)
    print('expected signal = ',e_b * lens_mean_absg / 2.)
    # The precision of this is a bit less though, since we now have more shape noise.
    # Naively, I would expect sqrt(2) worse, but since the agreement in this test is largely
    # artificial, as I placed the exact signal down with no shape noise, the increased shape
    # noise is a lot more than previously here.  So I had to drop the precision by a factor of
    # 5 relative to what I did above.
    numpy.testing.assert_almost_equal(gg.xim/(e_b * lens_mean_absg/2.)/10., 0.1, decimal=2)
    print('gg.xip = ',gg.xip)
    print('expected signal = ',e_a * lens_mean_absg / 2.)
    numpy.testing.assert_almost_equal(gg.xip/(e_a * lens_mean_absg/2.)/10, 0.1, decimal=2)



if __name__ == '__main__':
    test_gg()
    test_spherical()
    test_aardvark()
    test_shuffle()
    test_haloellip()
