/* $RCSfile$
 * $Author: miguelrojasch $
 * $Date: 2006-05-11 14:25:07 +0200 (Do, 11 Mai 2006) $
 * $Revision: 6221 $
 *
 *  Copyright (C) 2004-2007  Miguel Rojas <miguel.rojas@uni-koeln.de>
 * 
 * Contact: cdk-devel@lists.sourceforge.net
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public License
 * as published by the Free Software Foundation; either version 2.1
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA. 
 */
package org.openscience.cdk.reaction.type;


import java.util.Iterator;

import org.junit.Assert;
import org.junit.BeforeClass;
import org.junit.Test;
import org.openscience.cdk.CDKConstants;
import org.openscience.cdk.DefaultChemObjectBuilder;
import org.openscience.cdk.atomtype.CDKAtomTypeMatcher;
import org.openscience.cdk.exception.CDKException;
import org.openscience.cdk.interfaces.IAtom;
import org.openscience.cdk.interfaces.IBond;
import org.openscience.cdk.interfaces.IChemObjectBuilder;
import org.openscience.cdk.interfaces.IMolecule;
import org.openscience.cdk.interfaces.IMoleculeSet;
import org.openscience.cdk.interfaces.IReactionSet;
import org.openscience.cdk.isomorphism.UniversalIsomorphismTester;
import org.openscience.cdk.isomorphism.matchers.IQueryAtomContainer;
import org.openscience.cdk.isomorphism.matchers.QueryAtomContainer;
import org.openscience.cdk.isomorphism.matchers.QueryAtomContainerCreator;
import org.openscience.cdk.nonotify.NoNotificationChemObjectBuilder;
import org.openscience.cdk.reaction.IReactionProcess;
import org.openscience.cdk.reaction.type.HeterolyticCleavageSBReaction;
import org.openscience.cdk.reaction.type.SharingChargeDBReaction;
import org.openscience.cdk.reaction.ReactionProcessTest;
import org.openscience.cdk.tools.LonePairElectronChecker;
import org.openscience.cdk.tools.manipulator.AtomContainerManipulator;
import org.openscience.cdk.tools.manipulator.ReactionManipulator;

/**
 * TestSuite that runs a test for the SharingChargeDBReactionTest.
 * Generalized Reaction: [A+]=B => A|-[B+].
 *
 * @cdk.module test-reaction
 */
public class SharingChargeDBReactionTest extends ReactionProcessTest {

	private final static IChemObjectBuilder builder = NoNotificationChemObjectBuilder.getInstance();
	private final static LonePairElectronChecker lpcheck = new LonePairElectronChecker();
	/**
	 *  The JUnit setup method
	 */
	@BeforeClass public static void setUp() throws Exception {
	 	setReaction(SharingChargeDBReaction.class);
	}
	
	/**
	 * A unit test suite for JUnit. Reaction: C-C=[O+] => C-[C+]O|
	 * Automatic search of the center active.
	 *
	 * @return    The test suite
	 */
	@Test public void testAutomaticCentreActive() throws Exception {
		IReactionProcess type = new SharingChargeDBReaction();
		IMoleculeSet setOfReactants = DefaultChemObjectBuilder.getInstance().newMoleculeSet();
		/*C-C=[O+]*/
		IMolecule molecule = getMolecule1();
		setOfReactants.addMolecule(molecule);

		/* initiate */
		
        Object[] params = {Boolean.FALSE};
        type.setParameters(params);
        IReactionSet setOfReactions = type.initiate(setOfReactants, null);
        
        Assert.assertEquals(1, setOfReactions.getReactionCount());
        Assert.assertEquals(1, setOfReactions.getReaction(0).getProductCount());

        
        
        IMolecule product = setOfReactions.getReaction(0).getProducts().getMolecule(0);
        Assert.assertEquals(1, product.getAtom(1).getFormalCharge().intValue());
        Assert.assertEquals(0, product.getConnectedLonePairsCount(molecule.getAtom(1)));
        
		/*C[C+]O|*/
        IMolecule molecule2 = getMolecule2();
        
        IQueryAtomContainer queryAtom = QueryAtomContainerCreator.createSymbolAndChargeQueryContainer(product);
        Assert.assertTrue(UniversalIsomorphismTester.isIsomorph(molecule2,queryAtom));
	}
	/**
	 * A unit test suite for JUnit. Reaction: C-C=[O+] => C-[C+]O|
	 * Manually put of the center active.
	 *
	 * @return    The test suite
	 */
	@Test public void testManuallyCentreActive() throws Exception {
		IReactionProcess type = new SharingChargeDBReaction();
		IMoleculeSet setOfReactants = DefaultChemObjectBuilder.getInstance().newMoleculeSet();
		/*C-C=[O+]*/
		IMolecule molecule = getMolecule1();
		setOfReactants.addMolecule(molecule);
		
		/*manually put the center active*/
		molecule.getAtom(1).setFlag(CDKConstants.REACTIVE_CENTER,true);
		molecule.getAtom(2).setFlag(CDKConstants.REACTIVE_CENTER,true);
		molecule.getBond(1).setFlag(CDKConstants.REACTIVE_CENTER,true);

		
        Object[] params = {Boolean.TRUE};
        type.setParameters(params);

		/* initiate */
		
        IReactionSet setOfReactions = type.initiate(setOfReactants, null);
        
        Assert.assertEquals(1, setOfReactions.getReactionCount());
        Assert.assertEquals(1, setOfReactions.getReaction(0).getProductCount());

        IMolecule product = setOfReactions.getReaction(0).getProducts().getMolecule(0);
        
        /*C-[C+]O|*/
        IMolecule molecule2 = getMolecule2();
        
        IQueryAtomContainer queryAtom = QueryAtomContainerCreator.createSymbolAndChargeQueryContainer(product);
        Assert.assertTrue(UniversalIsomorphismTester.isIsomorph(molecule2,queryAtom));
	}

	/**
	 * A unit test suite for JUnit. 
	 * 
	 * @return    The test suite
	 */
	@Test public void testCentreActive() throws Exception {
		IReactionProcess type  = new SharingChargeDBReaction();

		Object[] object = type.getParameters();
		Assert.assertFalse(((Boolean) object[0]).booleanValue());
		 
		Object[] params = {Boolean.TRUE};
        type.setParameters(params);
		Assert.assertTrue(((Boolean) params[0]).booleanValue());
        
	}
	/**
	 * A unit test suite for JUnit.
	 * 
	 * @return    The test suite
	 */
	@Test public void testCDKConstants_REACTIVE_CENTER() throws Exception {
		IReactionProcess type  = new SharingChargeDBReaction();
		IMoleculeSet setOfReactants = builder.newMoleculeSet();

		IMolecule molecule = getMolecule1();
		
		/*manually put the reactive center*/
		molecule.getAtom(1).setFlag(CDKConstants.REACTIVE_CENTER,true);
		molecule.getAtom(2).setFlag(CDKConstants.REACTIVE_CENTER,true);
		molecule.getBond(1).setFlag(CDKConstants.REACTIVE_CENTER,true);
		
		setOfReactants.addMolecule(molecule);
		Object[] params = {Boolean.TRUE};
        type.setParameters(params);
        
        /* initiate */
        IReactionSet setOfReactions = type.initiate(setOfReactants, null);

        IMolecule reactant = setOfReactions.getReaction(0).getReactants().getMolecule(0);
		Assert.assertTrue(molecule.getAtom(1).getFlag(CDKConstants.REACTIVE_CENTER));
		Assert.assertTrue(reactant.getAtom(1).getFlag(CDKConstants.REACTIVE_CENTER));
		Assert.assertTrue(molecule.getAtom(2).getFlag(CDKConstants.REACTIVE_CENTER));
		Assert.assertTrue(reactant.getAtom(2).getFlag(CDKConstants.REACTIVE_CENTER));
		Assert.assertTrue(molecule.getBond(1).getFlag(CDKConstants.REACTIVE_CENTER));
		Assert.assertTrue(reactant.getBond(1).getFlag(CDKConstants.REACTIVE_CENTER));
	}

	/**
	 * A unit test suite for JUnit.
	 *  
	 * @return    The test suite
	 */
	@Test public void testMapping() throws Exception {
		IReactionProcess type = new SharingChargeDBReaction();
		IMoleculeSet setOfReactants = DefaultChemObjectBuilder.getInstance().newMoleculeSet();
		/*C-C=[O+]*/
		IMolecule molecule = getMolecule1();
		setOfReactants.addMolecule(molecule);
		
		/*automatic search of the center active*/
        Object[] params = {Boolean.FALSE};
        type.setParameters(params);

		/* initiate */
		
        IReactionSet setOfReactions = type.initiate(setOfReactants, null);
        
        IMolecule product = setOfReactions.getReaction(0).getProducts().getMolecule(0);

        Assert.assertEquals(3,setOfReactions.getReaction(0).getMappingCount());
        
        IAtom mappedProductA1 = (IAtom)ReactionManipulator.getMappedChemObject(setOfReactions.getReaction(0), molecule.getAtom(1));
        Assert.assertEquals(mappedProductA1, product.getAtom(1));
        IBond mappedProductB1 = (IBond)ReactionManipulator.getMappedChemObject(setOfReactions.getReaction(0), molecule.getBond(1));
        Assert.assertEquals(mappedProductB1, product.getBond(1));
        mappedProductA1 = (IAtom)ReactionManipulator.getMappedChemObject(setOfReactions.getReaction(0), molecule.getAtom(2));
        Assert.assertEquals(mappedProductA1, product.getAtom(2));
		
	}


	/**
	 * Test to recognize if this IMolecule_1 matches correctly into the CDKAtomTypes.
	 * @throws Exception 
	 * @throws ClassNotFoundException 
	 * @throws CDKException 
	 */
	@Test public void testAtomTypesMolecule1() throws CDKException, ClassNotFoundException, Exception{
		IMolecule moleculeTest = getMolecule1();
		makeSureAtomTypesAreRecognized(moleculeTest);
		
	}

	/**
	 * Test to recognize if this IMolecule_2 matches correctly into the CDKAtomTypes.
	 * @throws Exception 
	 * @throws ClassNotFoundException 
	 * @throws CDKException 
	 */
	@Test public void testAtomTypesMolecule2() throws CDKException, ClassNotFoundException, Exception{
		IMolecule moleculeTest = getMolecule2();
		makeSureAtomTypesAreRecognized(moleculeTest);
		
	}
	/**
	 * get the molecule 1: C-C=[O+]
	 * 
	 * @return The IMolecule
	 */
	private IMolecule getMolecule1()throws Exception {
		
		IMolecule molecule = builder.newMolecule();
		molecule.addAtom(builder.newAtom("C"));
		molecule.addAtom(builder.newAtom("C"));
		molecule.addBond(0, 1, IBond.Order.SINGLE);
		molecule.addAtom(builder.newAtom("O"));
		molecule.getAtom(2).setFormalCharge(1);
		molecule.addBond(1, 2, IBond.Order.DOUBLE);
		addExplicitHydrogens(molecule);
        
        LonePairElectronChecker lpcheck = new LonePairElectronChecker();
		AtomContainerManipulator.percieveAtomTypesAndConfigureAtoms(molecule);
        lpcheck.saturate(molecule);
        return molecule;
	}
	/**
	 * get the molecule 2: C[C+]O|
	 * 
	 * @return The IMolecule
	 */
	private IMolecule getMolecule2()throws Exception {
		IMolecule molecule = builder.newMolecule();
		molecule.addAtom(builder.newAtom("C"));
		molecule.addAtom(builder.newAtom("C"));
		molecule.getAtom(1).setFormalCharge(1);
		molecule.addBond(0, 1, IBond.Order.SINGLE);
		molecule.addAtom(builder.newAtom("O"));
		molecule.addBond(1, 2, IBond.Order.SINGLE);
		
		addExplicitHydrogens(molecule);
        LonePairElectronChecker lpcheck = new LonePairElectronChecker();
		AtomContainerManipulator.percieveAtomTypesAndConfigureAtoms(molecule);
        lpcheck.saturate(molecule);
        return molecule;
	}
	/**
	 * Test to recognize if a IMolecule matcher correctly the CDKAtomTypes.
	 * 
	 * @param molecule          The IMolecule to analyze
	 * @throws CDKException
	 */
	private void makeSureAtomTypesAreRecognized(IMolecule molecule) throws CDKException {

		Iterator<IAtom> atoms = molecule.atoms();
		CDKAtomTypeMatcher matcher = CDKAtomTypeMatcher.getInstance(molecule.getBuilder());
		while (atoms.hasNext()) {
				IAtom nextAtom = atoms.next();
				Assert.assertNotNull(
					"Missing atom type for: " + nextAtom, 
					matcher.findMatchingAtomType(molecule, nextAtom)
				);
		}
	}

	/**
	 * A unit test suite for JUnit. Reaction:.
	 * [N+]!#!C => N=[C+]
	 *
	 * @return    The test suite
	 */
	@Test public void testNspChargeTripleB() throws Exception {
		//Smiles("[N+]#C")
		IMolecule molecule = builder.newMolecule();
		molecule.addAtom(builder.newAtom("N"));
		molecule.addAtom(builder.newAtom("C"));
		molecule.getAtom(0).setFormalCharge(+1);
		molecule.addBond(0, 1, IBond.Order.TRIPLE);
		molecule.addAtom(builder.newAtom("H"));
		molecule.addAtom(builder.newAtom("H"));
		molecule.addBond(0, 2, IBond.Order.SINGLE);
		molecule.addBond(1, 3, IBond.Order.SINGLE);
        AtomContainerManipulator.percieveAtomTypesAndConfigureAtoms(molecule);
		lpcheck.saturate(molecule);
		
		molecule.getAtom(0).setFlag(CDKConstants.REACTIVE_CENTER,true);
		molecule.getAtom(1).setFlag(CDKConstants.REACTIVE_CENTER,true);
		molecule.getBond(0).setFlag(CDKConstants.REACTIVE_CENTER,true);

        IMoleculeSet setOfReactants = DefaultChemObjectBuilder.getInstance().newMoleculeSet();
        setOfReactants.addMolecule(molecule);
		
		IReactionProcess type  = new HeterolyticCleavageSBReaction(); 
		Object[] params = {Boolean.TRUE};
        type.setParameters(params);
        
        /* initiate */
		IReactionSet setOfReactions = type.initiate(setOfReactants, null);

        Assert.assertEquals(1, setOfReactions.getReactionCount());
        
        // expected products 

        //Smiles("N=[C+]")
        IMolecule expected1 = builder.newMolecule();
        expected1.addAtom(builder.newAtom("N"));
        expected1.addAtom(builder.newAtom("C"));
		expected1.getAtom(1).setFormalCharge(+1);
        expected1.addBond(0, 1, IBond.Order.DOUBLE);
        expected1.addAtom(builder.newAtom("H"));
        expected1.addAtom(builder.newAtom("H"));
        expected1.addBond(0, 2, IBond.Order.SINGLE);
        expected1.addBond(1, 3, IBond.Order.SINGLE);
        AtomContainerManipulator.percieveAtomTypesAndConfigureAtoms(expected1);
		lpcheck.saturate(expected1);
        IMolecule product1 = setOfReactions.getReaction(0).getProducts().getMolecule(0);
        QueryAtomContainer queryAtom = QueryAtomContainerCreator.createSymbolAndChargeQueryContainer(expected1);
        Assert.assertTrue(UniversalIsomorphismTester.isIsomorph(product1,queryAtom));
		
	}
}
