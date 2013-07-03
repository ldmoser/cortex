##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import gc
import sys
import math
import unittest

import IECore

class LinkedSceneTest( unittest.TestCase ) :

	@staticmethod
	def compareBBox( box1, box2 ):
		errorTolerance = IECore.V3d(1e-5, 1e-5, 1e-5)
		boxTmp = IECore.Box3d( box1.min - errorTolerance, box1.max + errorTolerance )
		if not boxTmp.contains( box2 ):
			return False
		boxTmp = IECore.Box3d( box2.min - errorTolerance, box2.max + errorTolerance )
		if not boxTmp.contains( box1 ):
			return False
		return True
	
	def testSupportedExtension( self ) :
		self.assertTrue( "lscc" in IECore.SceneInterface.supportedExtensions() )
		self.assertTrue( "lscc" in IECore.SceneInterface.supportedExtensions( IECore.IndexedIO.OpenMode.Read ) )
		self.assertTrue( "lscc" in IECore.SceneInterface.supportedExtensions( IECore.IndexedIO.OpenMode.Write ) )
		self.assertTrue( "lscc" in IECore.SceneInterface.supportedExtensions( IECore.IndexedIO.OpenMode.Write + IECore.IndexedIO.OpenMode.Read ) )
		self.assertFalse( "lscc" in IECore.SceneInterface.supportedExtensions( IECore.IndexedIO.OpenMode.Append ) )

	def testFactoryFunction( self ):
		# test Write factory function 
		m = IECore.SceneInterface.create( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Write )
		self.assertTrue( isinstance( m, IECore.LinkedScene ) )
		self.assertEqual( m.fileName(), "/tmp/test.lscc" )
		self.assertRaises( RuntimeError, m.readBound, 0.0 )
		del m
		# test Read factory function
		m = IECore.SceneInterface.create( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Read )
		self.assertTrue( isinstance( m, IECore.LinkedScene ) )
		self.assertEqual( m.fileName(), "/tmp/test.lscc" )
		m.readBound( 0.0 )

	def testConstructors( self ):

		# test Read from a previously opened scene.
		m = IECore.SceneCache( "test/IECore/data/sccFiles/animatedSpheres.scc", IECore.IndexedIO.OpenMode.Read )
		l = IECore.LinkedScene( m )
		# test Write mode
		m = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Write )
		self.assertTrue( isinstance( m, IECore.LinkedScene ) )
		self.assertEqual( m.fileName(), "/tmp/test.lscc" )
		self.assertRaises( RuntimeError, m.readBound, 0.0 )
		del m
		# test Read mode
		m = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Read )
		self.assertTrue( isinstance( m, IECore.LinkedScene ) )
		self.assertEqual( m.fileName(), "/tmp/test.lscc" )
		m.readBound( 0.0 )

	def testAppendRaises( self ) :
		self.assertRaises( RuntimeError, IECore.SceneInterface.create, "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Append )
		self.assertRaises( RuntimeError, IECore.LinkedScene, "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Append )

	def testReadNonExistentRaises( self ) :
		self.assertRaises( RuntimeError, IECore.LinkedScene, "iDontExist.lscc", IECore.IndexedIO.OpenMode.Read )

	def testLinkAttribute( self ):

		self.assertEqual( IECore.LinkedScene.linkAttribute, "sceneInterface:link" )

		m = IECore.SceneCache( "test/IECore/data/sccFiles/animatedSpheres.scc", IECore.IndexedIO.OpenMode.Read )
		attr = IECore.LinkedScene.linkAttributeData( m )
		expectedAttr = IECore.CompoundData( 
			{
				"fileName": IECore.StringData("test/IECore/data/sccFiles/animatedSpheres.scc"), 
				"root": IECore.InternedStringVectorData( [] )
			}
		)
		self.assertEqual( attr, expectedAttr )

		A = m.child("A")
		attr = IECore.LinkedScene.linkAttributeData( A )
		expectedAttr = IECore.CompoundData( 
			{
				"fileName": IECore.StringData("test/IECore/data/sccFiles/animatedSpheres.scc"), 
				"root": IECore.InternedStringVectorData( [ 'A' ] )
			}
		)
		self.assertEqual( attr, expectedAttr )

		A = m.child("A")
		attr = IECore.LinkedScene.linkAttributeData( A, 10.0 )
		expectedAttr['time'] = IECore.DoubleData(10.0)
		self.assertEqual( attr, expectedAttr )
		
	def testWriting( self ):

		m = IECore.SceneCache( "test/IECore/data/sccFiles/animatedSpheres.scc", IECore.IndexedIO.OpenMode.Read )
		A = m.child("A")

		l = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Write )
		i0 = l.createChild("instance0")
		i0.writeLink( m )
		i1 = l.createChild("instance1")
		i1.writeLink( m )
		i1.writeAttribute( "testAttr", IECore.StringData("test"), 0 )
		i1.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )
		i2 = l.createChild("instance2")
		i2.writeLink( A )
		i2.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ), 0.0 )
		self.assertRaises( RuntimeError, i2.createChild, "cannotHaveChildrenAtLinks" )
		i2.writeTags( ["canHaveTagsAtLinks"] )
		self.assertRaises( RuntimeError, i2.writeObject, IECore.SpherePrimitive( 1 ), 0.0 )  # cannot save objects at link locations.
		b1 = l.createChild("branch1")
		b1.writeObject( IECore.SpherePrimitive( 1 ), 0.0 )
		self.assertRaises( RuntimeError, b1.writeLink, A )
		b2 = l.createChild("branch2")
		c2 = b2.createChild("child2")
		self.assertRaises( RuntimeError, b2.writeLink, A )
		del i0, i1, i2, l, b1, b2, c2

		l = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Read )

		self.assertEqual( l.numBoundSamples(), 4 )
		self.assertEqual( set(l.childNames()), set(['instance0','instance1','instance2','branch1','branch2']) )
		i0 = l.child("instance0")
		self.assertEqual( i0.numBoundSamples(), 4 )
		self.failUnless( LinkedSceneTest.compareBBox( i0.readBoundAtSample(0), IECore.Box3d( IECore.V3d( -1,-1,-1 ), IECore.V3d( 2,2,1 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i0.readBoundAtSample(1), IECore.Box3d( IECore.V3d( -1,-1,-1 ), IECore.V3d( 3,3,1 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i0.readBoundAtSample(2), IECore.Box3d( IECore.V3d( -2,-1,-2 ), IECore.V3d( 4,5,2 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i0.readBoundAtSample(3), IECore.Box3d( IECore.V3d( -3,-1,-3 ), IECore.V3d( 4,6,3 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i0.readBound(0), IECore.Box3d( IECore.V3d( -1,-1,-1 ), IECore.V3d( 2,2,1 ) ) ) )

		A = i0.child("A")
		self.failUnless( LinkedSceneTest.compareBBox( A.readBoundAtSample(0), IECore.Box3d(IECore.V3d( -1,-1,-1 ), IECore.V3d( 1,1,1 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( A.readBoundAtSample(1), IECore.Box3d(IECore.V3d( -1,-1,-1 ), IECore.V3d( 1,1,1 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( A.readBoundAtSample(2), IECore.Box3d(IECore.V3d( 0,-1,-1 ), IECore.V3d( 2,1,1 ) ) ) )
		self.assertEqual( i0.readTransform( 0 ), IECore.M44dData( IECore.M44d() ) )

		i1 = l.child("instance1")
		self.assertEqual( i1.numBoundSamples(), 4 )
		self.failUnless( LinkedSceneTest.compareBBox( i1.readBoundAtSample(0), IECore.Box3d( IECore.V3d( -1,-1,-1 ), IECore.V3d( 2,2,1 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i1.readBoundAtSample(2), IECore.Box3d( IECore.V3d( -2,-1,-2 ), IECore.V3d( 4,5,2 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i1.readBoundAtSample(3), IECore.Box3d( IECore.V3d( -3,-1,-3 ), IECore.V3d( 4,6,3 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i1.readBound(0), IECore.Box3d( IECore.V3d( -1,-1,-1 ), IECore.V3d( 2,2,1 ) ) ) )
		self.assertEqual( i1.readTransform( 0 ), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ) )
		self.assertEqual( i1.readAttribute( "testAttr", 0 ), IECore.StringData("test") )
		
		i2 = l.child("instance2")
		self.assertEqual( i2.numBoundSamples(), 3 )
		self.failUnless( LinkedSceneTest.compareBBox( i2.readBoundAtSample(0), IECore.Box3d(IECore.V3d( -1,-1,-1 ), IECore.V3d( 1,1,1 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i2.readBoundAtSample(1), IECore.Box3d(IECore.V3d( -1,-1,-1 ), IECore.V3d( 1,1,1 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( i2.readBoundAtSample(2), IECore.Box3d(IECore.V3d( 0,-1,-1 ), IECore.V3d( 2,1,1 ) ) ) )
		self.assertEqual( i2.readTransform( 0 ), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ) )
		self.assertTrue( i2.hasTag( "canHaveTagsAtLinks" ) )
		self.assertTrue( l.hasTag( "canHaveTagsAtLinks" ) )	# tags propagate up
		self.assertTrue( i2.child("a").hasTag( "canHaveTagsAtLinks" ) )		# tags at link locations propagate down as well

		self.assertEqual( l.scene( [ 'instance0' ] ).path(), [ 'instance0' ] )
		self.assertEqual( l.scene( [ 'instance0', 'A' ] ).path(), [ 'instance0', 'A' ] )
		self.assertEqual( i0.path(), [ 'instance0' ] )

		# test saving a two level LinkedScene
		l2 = IECore.LinkedScene( "/tmp/test2.lscc", IECore.IndexedIO.OpenMode.Write )
		base = l2.createChild("base")
		t1 = base.createChild("test1")
		t1.writeLink( l )
		t2 = base.createChild("test2")
		t2.writeLink( i0 )
		t3 = base.createChild("test3")
		t3.writeLink( i1 )
		t4 = base.createChild("test4")
		t4.writeLink( i2 )
		t5 = base.createChild("test5")
		t5.writeLink( A )
		del l2, t1, t2, t3, t4, t5

	def testTimeRemapping( self ):

		m = IECore.SceneCache( "test/IECore/data/sccFiles/animatedSpheres.scc", IECore.IndexedIO.OpenMode.Read )

		l = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Write )
		# save animated spheres with double the speed and with offset, using less samples (time remapping)
		i0 = l.createChild("instance0")
		i0.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 0.0 ), 1.0 )
		i0.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 3.0 ), 2.0 )
		# save animated spheres with same speed and with offset, same samples (time remapping is identity)
		i1 = l.createChild("instance1")
		i1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 0.0 ), 1.0 )
		i1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 1.0 ), 2.0 )
		i1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 2.0 ), 3.0 )
		i1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 3.0 ), 4.0 )
		# save animated spheres with half the speed, adding more samples to a range of the original (time remapping)
		i2 = l.createChild("instance2")
		i2.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 0.0 ), 0.0 )
		i2.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 0.5 ), 1.0 )
		i2.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 1.0 ), 2.0 )

		del i0, i1, i2, l

		l = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Read )
		self.assertEqual( l.numBoundSamples(), 5 )
		i0 = l.child("instance0")
		self.assertEqual( i0.numBoundSamples(), 2 )
		self.assertEqual( i0.numTransformSamples(), 1 )
		self.assertEqual( i0.readTransformAtSample(0), IECore.M44dData() )
		A0 = i0.child("A")
		self.assertEqual( A0.numBoundSamples(), 2 )
		self.assertEqual( A0.numTransformSamples(), 2 )
		self.failUnless( LinkedSceneTest.compareBBox( A0.readBoundAtSample(0), IECore.Box3d(IECore.V3d( -1,-1,-1 ), IECore.V3d( 1,1,1 ) ) ) )
		self.failUnless( LinkedSceneTest.compareBBox( A0.readBoundAtSample(1), IECore.Box3d(IECore.V3d( 0,-1,-1 ), IECore.V3d( 2,1,1 ) ) ) )
		self.assertEqual( A0.readTransformAtSample(0), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ) )
		self.assertEqual( A0.readTransformAtSample(1), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ) )
		i1 = l.child("instance1")
		self.assertEqual( i1.numBoundSamples(), 4 )
		self.assertEqual( i1.numTransformSamples(), 1 )
		A1 = i1.child("A")
		self.assertEqual( A1.numTransformSamples(), 4 )
		self.assertEqual( A1.readTransformAtSample(0), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ) )
		self.assertEqual( A1.readTransformAtSample(1), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ) )
		self.assertEqual( A1.readTransformAtSample(2), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ) )
		self.assertEqual( A1.readTransformAtSample(3), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ) )
		i2 = l.child("instance2")
		self.assertEqual( i2.numBoundSamples(), 3 )
		self.assertEqual( i2.numTransformSamples(), 1 )
		A2 = i2.child("A")
		self.assertEqual( A2.numBoundSamples(), 3 )
		self.assertEqual( A2.numTransformSamples(), 3 )
		self.assertEqual( A2.readTransform(1.0), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1.5, 0, 0 ) ) ) )
		self.assertEqual( A2.readTransformAtSample(0), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ) )
		self.assertEqual( A2.readTransformAtSample(1), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1.5, 0, 0 ) ) ) )
		self.assertEqual( A2.readTransformAtSample(2), IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ) )
		
	def testLinkHash( self ):

		m = IECore.SceneCache( "test/IECore/data/sccFiles/animatedSpheres.scc", IECore.IndexedIO.OpenMode.Read )

		l = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Write )
		# save animated spheres with no time offset, but less samples
		i0 = l.createChild("instance0")
		i0.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 1.0 ), 1.0 )
		i0.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 2.0 ), 2.0 )
		# save animated spheres with same speed and no offset, same samples (time remapping is identity)
		i1 = l.createChild("instance1")
		i1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 0.0 ), 0.0 )
		i1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 1.0 ), 1.0 )
		i1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 2.0 ), 2.0 )
		i1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 3.0 ), 3.0 )
		# save animated spheres with same speed and with offset, same samples (time remapping is identity)
		i2 = l.createChild("instance2")
		i2.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 0.0 ), 1.0 )
		i2.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 1.0 ), 2.0 )
		i2.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 2.0 ), 3.0 )
		i2.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 3.0 ), 4.0 )
		# save non-animated link
		i3 = l.createChild("instance3")
		i3.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m ), 0.0 )
		# create a transform and have the same links as instance0 and instance3
		B = l.createChild("B")
		i0b = B.createChild("instance0")
		i0b.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 1.0 ), 1.0 )
		i0b.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m, 2.0 ), 2.0 )
		i3b = B.createChild("instance3")
		i3b.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( m ), 0.0 )
		C = l.createChild("C")
		
		del i0, i1, i2, i3, i0b, i3b, B, C, l

		# open first linked scene for reading...
		l = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Read )
		i0 = l.child("instance0")
		i1 = l.child("instance1")
		i2 = l.child("instance2")
		i3 = l.child("instance3")
		B = l.child("B")
		i0b = B.child("instance0")
		i3b = B.child("instance3")
		C = l.child("C")

		# create a second level of linked scene
		l2 =  IECore.LinkedScene( "/tmp/test2.lscc", IECore.IndexedIO.OpenMode.Write )
		# save animated spheres with no time offset, but less samples
		j0 = l2.createChild("link0")
		j0.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( l ), 0.0 )
		j1 = l2.createChild("link1")
		j1.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( l, 1 ), 0.0 )
		j2 = l2.createChild("link2")
		j2.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i0 ), 0.0 )
		j3 = l2.createChild("link3")
		j3.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i0, 1 ), 0.0 )
		j4 = l2.createChild("link4")
		j4.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i1 ), 0.0 )
		j5 = l2.createChild("link5")
		j5.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i1, 1 ), 0.0 )
		j6 = l2.createChild("link6")
		j6.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i2 ), 0.0 )
		j7 = l2.createChild("link7")
		j7.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i2, 1 ), 0.0 )
		j8 = l2.createChild("link8")
		j8.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i3 ), 0.0 )
		j9 = l2.createChild("link9")
		j9.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i3, 1 ), 0.0 )
		j10 = l2.createChild("link10")
		j10.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i0b ), 0.0 )
		j11 = l2.createChild("link11")
		j11.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i0b, 1 ), 0.0 )
		j12 = l2.createChild("link12")
		j12.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i3b ), 0.0 )
		j13 = l2.createChild("link13")
		j13.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( i3b, 1 ), 0.0 )
		j14 = l2.createChild("link14")
		j14.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( B ), 0.0 )
		j15 = l2.createChild("link15")
		j15.writeAttribute( IECore.LinkedScene.linkAttribute, IECore.LinkedScene.linkAttributeData( C ), 0.0 )

		del j0,j1,j2,j3,j4,j5,j6,j7,j8,j9,j10,j11,j12,j13,j14,j15,l2

		# open second linked scene for reading..
		l2 = IECore.LinkedScene( "/tmp/test2.lscc", IECore.IndexedIO.OpenMode.Read )
		j0 = l2.child("link0")
		j1 = l2.child("link1")
		j2 = l2.child("link2")
		j3 = l2.child("link3")
		j4 = l2.child("link4")
		j5 = l2.child("link5")
		j6 = l2.child("link6")
		j7 = l2.child("link7")
		j8 = l2.child("link8")
		j9 = l2.child("link9")
		j10 = l2.child("link10")
		j11 = l2.child("link11")
		j12 = l2.child("link12")
		j13 = l2.child("link13")
		j14 = l2.child("link14")
		j15 = l2.child("link15")

		self.assertTrue( j0.hasAttribute(  IECore.LinkedScene.linkHashAttribute ) )
		self.assertTrue( j13.hasAttribute(  IECore.LinkedScene.linkHashAttribute ) )
		self.assertTrue( j14.hasAttribute(  IECore.LinkedScene.linkHashAttribute ) )
		self.assertTrue( j15.hasAttribute(  IECore.LinkedScene.linkHashAttribute ) )
		self.assertFalse( l.hasAttribute( IECore.LinkedScene.linkHashAttribute ) )
		self.assertFalse( l2.hasAttribute( IECore.LinkedScene.linkHashAttribute ) )
		self.assertFalse( B.hasAttribute( IECore.LinkedScene.linkHashAttribute ) )
		self.assertFalse( C.hasAttribute( IECore.LinkedScene.linkHashAttribute ) )

		hashes = map( lambda s: s.readAttribute( IECore.LinkedScene.linkHashAttribute, 0 ).value, [ i0, i1, i2, i3, i0b, i3b,  j0, j1, j2, j3, j4, j5, j6, j7, j8, j9, j10, j11, j12, j13, j14, j15 ] )
		self.assertEqual( hashes, [
			'76af06504f2ed9dc99a2a0296800fcec',  		# link to instance0 
			'0de7db4782e9ac8156a7ce9ca1d9c282',  		# link to instance1
			'dfccdfc6a154547d5fabe4d66f6b81a0',  			# link to instance2 
			'9c70dc0a1f23a28312ee2697f011554c',  		# link to instance3
			'76af06504f2ed9dc99a2a0296800fcec',  		# link to B/instance0
			'9c70dc0a1f23a28312ee2697f011554c',  		# link to B/instance3
			'80dac5c2fb4a6d47f6af7e885d07779d', 'c43c6cbce3c0781b400e9bd10910737a', 	# links to l (no time, remapped)
			'76af06504f2ed9dc99a2a0296800fcec', 'e932e4f0cc42cea9c01093a4a01b2b57', 	# links to instance0 (no time, remapped)
			'0de7db4782e9ac8156a7ce9ca1d9c282', 'bf687671afed325aa4fef99702920faa', 	# links to instance1 (no time, remapped)
			'dfccdfc6a154547d5fabe4d66f6b81a0', 'b2ce41f20ef4a43e00339f8b2ea157aa', 		# links to instance2 (no time, remapped)
			'9c70dc0a1f23a28312ee2697f011554c', '3fb4f7f029452a06579e6dbe27a9a88a',	# links to instance3 (no time, remapped)
			'76af06504f2ed9dc99a2a0296800fcec', 'e932e4f0cc42cea9c01093a4a01b2b57', 	# links to B/instance1 (no time, remapped)
			'9c70dc0a1f23a28312ee2697f011554c', '3fb4f7f029452a06579e6dbe27a9a88a', 	# links to B/instance3 (no time, remapped)
			'c1046a0a73c11a5cf592fb733e848424',  	# link to B
			'6df4e880b6e589e37dbcf174a6ba0848'		# link to C
			]
		)


	def testReading( self ):

		def recurseCompare( basePath, virtualScene, realScene, atLink = True ) :
			self.assertEqual( basePath, virtualScene.path() )

			if not atLink :	# attributes and tranforms at link location are not loaded.

				self.assertEqual( set(virtualScene.attributeNames()), set(realScene.attributeNames()) )
				for attr in realScene.attributeNames() :
					self.assertTrue( virtualScene.hasAttribute( attr ) )
					self.assertEqual( virtualScene.numAttributeSamples(attr), realScene.numAttributeSamples(attr) )
					for s in xrange(0,virtualScene.numAttributeSamples(attr)) :
						self.assertEqual( virtualScene.readAttributeAtSample(attr, s), realScene.readAttributeAtSample(attr, s) )

				self.assertEqual( virtualScene.numTransformSamples(), realScene.numTransformSamples() )
				for s in xrange(0,virtualScene.numTransformSamples()) :
					self.assertEqual( virtualScene.readTransformAtSample(s), realScene.readTransformAtSample(s) )

			self.assertEqual( virtualScene.numBoundSamples(), realScene.numBoundSamples() )
			for s in xrange(0,virtualScene.numBoundSamples()) :
				self.assertEqual( virtualScene.readBoundAtSample(s), realScene.readBoundAtSample(s) )

			self.assertEqual( virtualScene.hasObject(), realScene.hasObject() )
			if virtualScene.hasObject() :
				self.assertEqual( virtualScene.numObjectSamples(), realScene.numObjectSamples() )
				for s in xrange(0,virtualScene.numObjectSamples()) :
					self.assertEqual( virtualScene.readObjectAtSample(s), realScene.readObjectAtSample(s) )

			self.assertEqual( set(virtualScene.childNames()), set(realScene.childNames()) )
			for c in virtualScene.childNames() :
				self.assertTrue( virtualScene.hasChild(c) )
				recurseCompare( basePath + [ str(c) ], virtualScene.child(c), realScene.child(c), False )

		env = IECore.LinkedScene( "test/IECore/data/sccFiles/environment.lscc", IECore.IndexedIO.OpenMode.Read )
		l = IECore.LinkedScene( "test/IECore/data/sccFiles/instancedSpheres.lscc", IECore.IndexedIO.OpenMode.Read )
		m = IECore.SceneCache( "test/IECore/data/sccFiles/animatedSpheres.scc", IECore.IndexedIO.OpenMode.Read )

		base = env.child('base')
		self.assertEqual( set(base.childNames()), set(['test1','test2','test3','test4','test5']) )
		test1 = base.child('test1')
		self.assertEqual( test1.path(), [ "base", "test1" ] )
		recurseCompare( test1.path(), test1, l )
		test2 = base.child('test2')
		self.assertEqual( test2.path(), [ "base", "test2" ] )
		recurseCompare( test2.path(), test2, l.child('instance0') )
		test3 = base.child('test3')
		self.assertEqual( test3.path(), [ "base", "test3" ] )
		recurseCompare( test3.path(), test3, l.child('instance1') )
		test4 = base.child('test4')
		self.assertEqual( test4.path(), [ "base", "test4" ] )
		recurseCompare( test4.path(), test4, l.child('instance2') )
		test5 = base.child('test5')
		self.assertEqual( test5.path(), [ "base", "test5" ] )
		recurseCompare( test5.path(), test5, l.child('instance1').child('A') )
		
		self.assertEqual( test1.child('instance0').path(), [ "base", "test1", "instance0" ] )
		recurseCompare( test1.child('instance0').path(), test1.child('instance0'), m )
		recurseCompare( test2.path(), test2, m )
		recurseCompare( test3.path(), test3, m )
		recurseCompare( test4.path(), test4, m.child('A') )
		recurseCompare( test5.path(), test5, m.child('A') )

		recurseCompare( test1.path(), env.scene( [ 'base', 'test1' ] ), l )
		recurseCompare( test1.path(), env.scene( [ 'base' ] ).child( 'test1' ), l )

	def testTags( self ) :

		def testSet( values ):
			return set( map( lambda s: IECore.InternedString(s), values ) )

		# create a base scene
		l = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Write )
		a = l.createChild('a')
		a.writeTags( [ "test" ] )
		l.writeTags( [ "tags" ] )
		del a, l

		# now create a linked scene that should inherit the tags from the base one, plus add other ones
		l = IECore.LinkedScene( "/tmp/test.lscc", IECore.IndexedIO.OpenMode.Read )
		a = l.child('a')

		self.assertEqual( set(l.readTags()), testSet(["test","tags"]) )
		self.assertEqual( set(l.readTags(includeChildren=False)), testSet(["tags"]) )
		self.assertEqual( set(a.readTags()), testSet(["test"]) )
		self.assertEqual( set(a.readTags(includeChildren=False)), testSet(["test"]) )

		l2 = IECore.LinkedScene( "/tmp/test2.lscc", IECore.IndexedIO.OpenMode.Write )

		A = l2.createChild('A')
		A.writeLink( l )
		A.writeTags( ['linkedA'] )	# creating tag after link

		B = l2.createChild('B')
		B.writeLink( a )

		C = l2.createChild('C')
		c = C.createChild('c')
		c.writeLink( l )
		C.writeTags( [ 'C' ] )

		D = l2.createChild('D')
		D.writeTags( [ 'D' ] )
		D.writeLink( a )	# creating link after tag

		del l, a, l2, A, B, C, c, D

		l2 = IECore.LinkedScene( "/tmp/test2.lscc", IECore.IndexedIO.OpenMode.Read )
		A = l2.child("A")
		Aa = A.child("a")
		B = l2.child("B")
		C = l2.child("C")
		c = C.child("c")
		ca = c.child("a")
		D = l2.child("D")

		self.assertTrue( l2.hasTag("test") )
		self.assertFalse( l2.hasTag("t") )
		self.assertEqual( set(l2.readTags()), testSet(["test","tags","C", "D","linkedA"]) )
		self.assertEqual( set(l2.readTags(includeChildren=False)), testSet([]) )
		self.assertEqual( set(A.readTags()), testSet(["test","tags","linkedA"]) )
		self.assertTrue( A.hasTag( "linkedA" ) )
		self.assertTrue( A.hasTag( "tags" ) )
		self.assertTrue( A.hasTag( "test" ) )
		self.assertFalse( A.hasTag("C") )
		self.assertEqual( set(A.readTags(includeChildren=False)), testSet(["tags","linkedA"]) )
		self.assertEqual( set(Aa.readTags()), testSet(["test", "linkedA"]) )
		self.assertEqual( set(Aa.readTags(includeChildren=False)), testSet(["test"]) )
		self.assertEqual( set(B.readTags()), testSet(["test"]) )
		self.assertEqual( set(C.readTags()), testSet(["test","tags","C"]) )
		self.assertEqual( set(C.readTags(includeChildren=False)), testSet(["C"]) )
		self.assertEqual( set(c.readTags()), testSet(["test","tags"]) )
		self.assertEqual( set(c.readTags(includeChildren=False)), testSet(["tags"]) )
		self.assertEqual( set(ca.readTags()), testSet(["test"]) )
		self.assertEqual( set(C.readTags(includeChildren=False)), testSet(["C"]) )
		self.assertEqual( set(D.readTags()), testSet(["D", "test"]) )

if __name__ == "__main__":
	unittest.main()

