/* RandomGenerator.java
 * 
 * $RCSfile$    $Author$    $Date$    $Revision$
 * 
 * Copyright (C) 1997-2001  The Chemistry Development Kit (CDK) project
 * 
 * Contact: steinbeck@ice.mpg.de, gezelter@maul.chem.nd.edu, egonw@sci.kun.nl
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public License
 * as published by the Free Software Foundation; either version 2.1
 * of the License, or (at your option) any later version.
 * All we ask is that proper credit is given for our work, which includes
 * - but is not limited to - adding the above copyright notice to the beginning
 * of your source code files, and to any copyright notice that you may distribute
 * with programs based on this work.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *  
 */

package org.openscience.cdk.structgen;

import org.openscience.cdk.*;
import org.openscience.cdk.tools.*;

import java.util.Vector;

/**
 * RandomGenerator is a generator of Constitutional Isomers. It needs to be 
 * provided with a starting constitution and it makes random moves in 
 * constitutional space from there. 
 * This generator was first suggested by
 * Faulon, J.-L. Journal of Chemical Information and Computer Sciences 1996, 36, 731-740. 
 * 
 **/
 
public class RandomGenerator
{
	private Molecule proposedStructure = null;
	private Molecule molecule = null;
	private ConnectivityChecker cc = null; 
	private Vector bonds = null;
	public boolean debug = false;
	private int[] correctBondOrderSums;

	/**
	 * The empty contructor
	 */
	public RandomGenerator()
	{
		cc = new ConnectivityChecker();
	}


	/**
	 * Constructs a RandomGenerator with a given starting structure
	 *
	 * @param   molecule  The starting structure
	 */
	public RandomGenerator(Molecule molecule)
	{
		this ();
		setMolecule(molecule);
	}


	/**
	 * Proposes a structure which can be accepted or rejected by an external 
	 * entity. If rejected, the structure is not used as a starting point 
	 * for the next random move in structure space.
	 *
	 * @return A proposed molecule    
	 */
	public Molecule proposeStructure()
	{
		Molecule trial = new Molecule();
		trial.removeAllElements();
		trial.add(molecule);
		do
		{
			mutate(trial);
		}
		while(!(cc.isConnected(trial) && chemConstraintsOk(trial)));
		proposedStructure = trial;
		if (debug)
		{
			String s = "BondCounts:    ";
			for (int f = 0; f < trial.getAtomCount(); f++)
			{
				s += trial.getBondCount(trial.getAtomAt(f)) + " ";
			}
			System.out.println(s);
			s = "BondOrderSums: ";
			for (int f = 0; f < trial.getAtomCount(); f++)
			{
				s += trial.getBondOrderSum(trial.getAtomAt(f)) + " ";
			}
			System.out.println(s);
		}
		
		return proposedStructure;
	}

	/**
	 * Tell the RandomGenerator to accept the last structure that had been proposed
	 */
	public void acceptStructure()
	{
		if (proposedStructure != null)
		{
			molecule.removeAllBonds();
			for (int f = 0; f < proposedStructure.getBondCount(); f++)
			{
				molecule.addBond((Bond)proposedStructure.getBondAt(f).clone());
			}
		}
	}
	
	
	/**
	 * Randomly chooses four atoms and alters the bonding
	 * pattern between them according to rules described 
	 * in "Faulon, JCICS 1996, 36, 731"
	 */
	protected void mutate(AtomContainer ac)
	{
		int nrOfAtoms = ac.getAtomCount();
		int x1 = 0, x2 = 0, y1 = 0, y2 = 0, a11 = 0, a12 = 0, a22 = 0, a21 = 0;
		int b11 = 0, lowerborder = 0, upperborder = 0;

		Atom ax1 = null, ax2 = null, ay1 = null, ay2  = null;
		Bond b1 = null, b2 = null, b3 = null, b4 = null;
		int[] choices = new int[3];
		int choiceCounter  = 0;
		/* We need at least two non-zero bonds in order to be successful */
		int nonZeroBondsCounter = 0;
		do
		{
			do
			{
				nonZeroBondsCounter = 0;
				/* Randomly choose four distinct atoms */
				do
				{
					// this yields numbers between 0 and (nrOfAtoms - 1)
					x1 = (int)(Math.random() * nrOfAtoms);
					x2 = (int)(Math.random() * nrOfAtoms);
					y1 = (int)(Math.random() * nrOfAtoms);
					y2 = (int)(Math.random() * nrOfAtoms);
				}
				while (!(x1 != x2 && x1 != y1 && x1 != y2 && x2 != y1 && x2 != y2 && y1 != y2));
				ax1 = ac.getAtomAt(x1);
				ay1 = ac.getAtomAt(y1);
				ax2 = ac.getAtomAt(x2);
				ay2 = ac.getAtomAt(y2);
				/* Get four bonds for these four atoms */
				
				b1 = ac.getBond(ax1, ay1);
				if (b1 != null)
				{
					a11 = b1.getOrder();
					nonZeroBondsCounter ++;				
				}
				else
				{
					a11 = 0;
				}
				
				b2 = ac.getBond(ax1, ay2);
				if (b2 != null)
				{
					a12 = b2.getOrder();
					nonZeroBondsCounter ++;				
				}
				else
				{
					a12 = 0;
				}

				b3 = ac.getBond(ax2, ay1);
				if (b3 != null)
				{
					a21 = b3.getOrder();
					nonZeroBondsCounter ++;				
				}
				else
				{
					a21 = 0;
				}
				
				b4 = ac.getBond(ax2, ay2);									
				if (b4 != null)
				{
					a22 = b4.getOrder();
					nonZeroBondsCounter ++;
				}
				else
				{
					a22 = 0;
				}
			}while(nonZeroBondsCounter < 2);
			
					
			/* Compute the range for b11 (see Faulons formulae for details) */
			int[] cmax = {0, a11 - a22, a11 + a12 - 3, a11 + a21 - 3};
			int[] cmin = {3, a11 + a12, a11 + a21, a11 - a22 + 3};
			lowerborder = max(cmax);
			upperborder = min(cmin);
			/* Randomly choose b11 != a11 in the range max > r > min */
			if (debug) 				
			{
				System.out.println("*** New Try ***");
				System.out.println("a11 = " + a11);
				System.out.println("upperborder = " + upperborder);
				System.out.println("lowerborder = " + lowerborder);
			}
			choiceCounter = 0;
			for (int f = lowerborder; f <= upperborder; f++)
			{
				if (f != a11)
				{
					choices[choiceCounter] = f;
					choiceCounter ++;
				}
			}
			if (choiceCounter > 0)
			{
				b11 = choices[(int)(Math.random() * choiceCounter)];
			}

			if (debug) 				
			{
				System.out.println("b11 = " + b11);
			}

		}
		while (!(b11 != a11 && (b11 >= lowerborder && b11 <= upperborder)));

		int b12 = a11 + a12 - b11;
		int b21 = a11 + a21 - b11;
		int b22 = a22 - a11 + b11;
		
		
		if (b11 > 0)
		{
			if (b1 == null)
			{
				b1 = new Bond(ax1, ay1, b11);
				ac.addBond(b1);
			}
			else
			{
				b1.setOrder(b11);
			}
		}
		else if (b1 != null)
		{
			ac.removeBond(b1);
		}
		
		if (b12 > 0) 
		{
			if (b2 == null)
			{
				b2 = new Bond(ax1, ay2, b12);
				ac.addBond(b2);
			}
			else
			{
				b2.setOrder(b12);
			}
		}
		else if (b2 != null)
		{
			ac.removeBond(b2);
		}
		
		if (b21 > 0) 
		{
			if (b3 == null)
			{
				b3 = new Bond(ax2, ay1, b21);
				ac.addBond(b3);
			}
			else
			{
				b3.setOrder(b21);
			}
		}
		else if (b3 != null)
		{
			ac.removeBond(b3);
		}

		if (b22 > 0) 
		{
			if (b4 == null)
			{
				b4 = new Bond(ax2, ay2, b22);
				ac.addBond(b4);
			}
			else
			{
				b4.setOrder(b22);
			}
		}
		else if (b4 != null)
		{
			ac.removeBond(b4);
		}
		
		if (debug) 
		{				
			System.out.println("a11 a12 a21 a22: " + a11 + " " + a12 + " " + a21 + " " + a22);
			System.out.println("b11 b12 b21 b22: " + b11 + " " + b12 + " " + b21 + " " + b22);
		}
	}

	protected boolean chemConstraintsOk(Molecule test)
	{
		for (int f = 0; f < test.getAtomCount(); f++)
		{
			if (test.getBondOrderSum(test.getAtomAt(f)) != correctBondOrderSums[f])
			{
				return false;
			}
		}
		return true;
	}

	/**
	 * Analog of Math.max that returns the largest int value in an array of ints
	 *
	 * @param   values  the values to be searched for the largest value among them
	 * @return   the largest value among a set of given values  
	 */
	protected int max(int[] values)
	{
		int max = values[0];
		for (int f = 0; f < values.length; f++)
		{
			if (values[f] > max)
			{
				max = values[f];
			}
		}
		return max;
	}

	/**
	 * Analog of Math.min that returns the largest int value in an array of ints
	 *
	 * @param   values  the values to be searched for the smallest value among them
	 * @return   the smallest value among a set of given values  
	 */
	protected int min(int[] values)
	{
		int min = values[0];
		for (int f = 0; f < values.length; f++)
		{
			if (values[f] < min)
			{
				min = values[f];
			}
		}
		return min;
	}

	
	/**
	 * Assigns a starting structure to this generator
	 *
	 * @param   molecule  a starting structure for this generator
	 */
	public void setMolecule(Molecule mol)
	{
		this.molecule = mol;	
		initBondOrderSums(mol);
	}


	/**
	 * Returns the molecule which reflects the current state of this
	 * Stochastic Structure Generator
	 *
	 * @return The molecule    
	 */
	public Molecule getMolecule()
	{
		return this.molecule;
	}
	
	protected void initBondOrderSums(Molecule mol)
	{	
		correctBondOrderSums = new int[mol.getAtomCount()];
		for (int f = 0; f < mol.getAtomCount(); f++)
		{
			correctBondOrderSums[f] = mol.getBondOrderSum(mol.getAtomAt(f));
		}
	}

}
