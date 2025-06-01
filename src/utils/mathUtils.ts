/**
 * Mathematical Utilities for Quantum Computing
 * 
 * This file provides essential mathematical operations for quantum computing,
 * including complex number operations, matrix manipulations, and statistical
 * functions for quantum resource estimation and error analysis.
 */

// ======== Complex Numbers ========

/**
 * Complex number class for quantum state calculations
 */
export class Complex {
  constructor(
    public readonly real: number,
    public readonly imag: number
  ) {}

  /**
   * Create a complex number from polar coordinates
   * @param r Radius (magnitude)
   * @param theta Angle in radians
   */
  static fromPolar(r: number, theta: number): Complex {
    return new Complex(
      r * Math.cos(theta),
      r * Math.sin(theta)
    );
  }

  /**
   * Add two complex numbers
   */
  add(other: Complex): Complex {
    return new Complex(
      this.real + other.real,
      this.imag + other.imag
    );
  }

  /**
   * Subtract another complex number from this one
   */
  subtract(other: Complex): Complex {
    return new Complex(
      this.real - other.real,
      this.imag - other.imag
    );
  }

  /**
   * Multiply by another complex number
   */
  multiply(other: Complex): Complex {
    return new Complex(
      this.real * other.real - this.imag * other.imag,
      this.real * other.imag + this.imag * other.real
    );
  }

  /**
   * Multiply by a scalar
   */
  scale(scalar: number): Complex {
    return new Complex(
      this.real * scalar,
      this.imag * scalar
    );
  }

  /**
   * Divide by another complex number
   */
  divide(other: Complex): Complex {
    const denominator = other.real * other.real + other.imag * other.imag;
    return new Complex(
      (this.real * other.real + this.imag * other.imag) / denominator,
      (this.imag * other.real - this.real * other.imag) / denominator
    );
  }

  /**
   * Get the complex conjugate
   */
  conjugate(): Complex {
    return new Complex(this.real, -this.imag);
  }

  /**
   * Get the magnitude (absolute value) squared
   */
  magnitudeSquared(): number {
    return this.real * this.real + this.imag * this.imag;
  }

  /**
   * Get the magnitude (absolute value)
   */
  magnitude(): number {
    return Math.sqrt(this.magnitudeSquared());
  }

  /**
   * Get the phase (argument) in radians
   */
  phase(): number {
    return Math.atan2(this.imag, this.real);
  }

  /**
   * Check if equal to another complex number within a tolerance
   */
  equals(other: Complex, tolerance: number = 1e-10): boolean {
    return (
      Math.abs(this.real - other.real) < tolerance &&
      Math.abs(this.imag - other.imag) < tolerance
    );
  }

  /**
   * Convert to string representation
   */
  toString(): string {
    if (this.imag === 0) return `${this.real}`;
    if (this.real === 0) return `${this.imag}i`;
    const sign = this.imag < 0 ? '-' : '+';
    return `${this.real} ${sign} ${Math.abs(this.imag)}i`;
  }
}

// Common complex constants
export const COMPLEX_ZERO = new Complex(0, 0);
export const COMPLEX_ONE = new Complex(1, 0);
export const COMPLEX_I = new Complex(0, 1);

// ======== Matrix Operations ========

/**
 * Matrix class for quantum gate operations
 */
export class Matrix {
  /**
   * Create a matrix from a 2D array of complex numbers
   */
  constructor(public readonly data: Complex[][]) {
    // Validate matrix dimensions
    const rows = data.length;
    if (rows === 0) {
      throw new Error("Matrix cannot be empty");
    }
    
    const cols = data[0].length;
    for (let i = 1; i < rows; i++) {
      if (data[i].length !== cols) {
        throw new Error("All rows must have the same length");
      }
    }
  }

  /**
   * Get the number of rows
   */
  get rows(): number {
    return this.data.length;
  }

  /**
   * Get the number of columns
   */
  get cols(): number {
    return this.data[0].length;
  }

  /**
   * Create an identity matrix of given size
   */
  static identity(size: number): Matrix {
    const data: Complex[][] = [];
    for (let i = 0; i < size; i++) {
      data[i] = [];
      for (let j = 0; j < size; j++) {
        data[i][j] = i === j ? COMPLEX_ONE : COMPLEX_ZERO;
      }
    }
    return new Matrix(data);
  }

  /**
   * Create a zero matrix of given dimensions
   */
  static zeros(rows: number, cols: number): Matrix {
    const data: Complex[][] = [];
    for (let i = 0; i < rows; i++) {
      data[i] = [];
      for (let j = 0; j < cols; j++) {
        data[i][j] = COMPLEX_ZERO;
      }
    }
    return new Matrix(data);
  }

  /**
   * Add another matrix to this one
   */
  add(other: Matrix): Matrix {
    if (this.rows !== other.rows || this.cols !== other.cols) {
      throw new Error("Matrix dimensions must match for addition");
    }

    const result: Complex[][] = [];
    for (let i = 0; i < this.rows; i++) {
      result[i] = [];
      for (let j = 0; j < this.cols; j++) {
        result[i][j] = this.data[i][j].add(other.data[i][j]);
      }
    }
    return new Matrix(result);
  }

  /**
   * Subtract another matrix from this one
   */
  subtract(other: Matrix): Matrix {
    if (this.rows !== other.rows || this.cols !== other.cols) {
      throw new Error("Matrix dimensions must match for subtraction");
    }

    const result: Complex[][] = [];
    for (let i = 0; i < this.rows; i++) {
      result[i] = [];
      for (let j = 0; j < this.cols; j++) {
        result[i][j] = this.data[i][j].subtract(other.data[i][j]);
      }
    }
    return new Matrix(result);
  }

  /**
   * Multiply by another matrix
   */
  multiply(other: Matrix): Matrix {
    if (this.cols !== other.rows) {
      throw new Error("Matrix dimensions incompatible for multiplication");
    }

    const result: Complex[][] = [];
    for (let i = 0; i < this.rows; i++) {
      result[i] = [];
      for (let j = 0; j < other.cols; j++) {
        let sum = COMPLEX_ZERO;
        for (let k = 0; k < this.cols; k++) {
          sum = sum.add(this.data[i][k].multiply(other.data[k][j]));
        }
        result[i][j] = sum;
      }
    }
    return new Matrix(result);
  }

  /**
   * Scale matrix by a complex number
   */
  scale(scalar: Complex): Matrix {
    const result: Complex[][] = [];
    for (let i = 0; i < this.rows; i++) {
      result[i] = [];
      for (let j = 0; j < this.cols; j++) {
        result[i][j] = this.data[i][j].multiply(scalar);
      }
    }
    return new Matrix(result);
  }

  /**
   * Calculate the tensor product with another matrix
   * Essential for combining quantum gates
   */
  tensorProduct(other: Matrix): Matrix {
    const resultRows = this.rows * other.rows;
    const resultCols = this.cols * other.cols;
    const result: Complex[][] = [];

    for (let i = 0; i < resultRows; i++) {
      result[i] = [];
      for (let j = 0; j < resultCols; j++) {
        const thisRow = Math.floor(i / other.rows);
        const thisCol = Math.floor(j / other.cols);
        const otherRow = i % other.rows;
        const otherCol = j % other.cols;
        
        result[i][j] = this.data[thisRow][thisCol].multiply(
          other.data[otherRow][otherCol]
        );
      }
    }
    return new Matrix(result);
  }

  /**
   * Calculate the conjugate transpose (adjoint)
   */
  adjoint(): Matrix {
    const result: Complex[][] = [];
    for (let j = 0; j < this.cols; j++) {
      result[j] = [];
      for (let i = 0; i < this.rows; i++) {
        result[j][i] = this.data[i][j].conjugate();
      }
    }
    return new Matrix(result);
  }

  /**
   * Check if the matrix is unitary
   * A matrix is unitary if M * M† = I
   */
  isUnitary(tolerance: number = 1e-10): boolean {
    if (this.rows !== this.cols) {
      return false; // Unitary matrices must be square
    }

    const adjoint = this.adjoint();
    const product = this.multiply(adjoint);
    const identity = Matrix.identity(this.rows);

    // Check if product is approximately identity
    for (let i = 0; i < this.rows; i++) {
      for (let j = 0; j < this.cols; j++) {
        if (!product.data[i][j].equals(identity.data[i][j], tolerance)) {
          return false;
        }
      }
    }
    return true;
  }

  /**
   * Check if the matrix is Hermitian
   * A matrix is Hermitian if M = M†
   */
  isHermitian(tolerance: number = 1e-10): boolean {
    if (this.rows !== this.cols) {
      return false; // Hermitian matrices must be square
    }

    const adjoint = this.adjoint();
    
    // Check if matrix equals its adjoint
    for (let i = 0; i < this.rows; i++) {
      for (let j = 0; j < this.cols; j++) {
        if (!this.data[i][j].equals(adjoint.data[i][j], tolerance)) {
          return false;
        }
      }
    }
    return true;
  }

  /**
   * Calculate the trace of the matrix
   */
  trace(): Complex {
    if (this.rows !== this.cols) {
      throw new Error("Trace is only defined for square matrices");
    }

    let sum = COMPLEX_ZERO;
    for (let i = 0; i < this.rows; i++) {
      sum = sum.add(this.data[i][i]);
    }
    return sum;
  }

  /**
   * Apply the matrix to a state vector
   * @param state Array of complex numbers representing a quantum state
   */
  apply(state: Complex[]): Complex[] {
    if (state.length !== this.cols) {
      throw new Error("State vector length must match matrix columns");
    }

    const result: Complex[] = [];
    for (let i = 0; i < this.rows; i++) {
      let sum = COMPLEX_ZERO;
      for (let j = 0; j < this.cols; j++) {
        sum = sum.add(this.data[i][j].multiply(state[j]));
      }
      result.push(sum);
    }
    return result;
  }
}

// ======== Common Quantum Gates ========

/**
 * Common single-qubit quantum gates as matrices
 */
export const QuantumGates = {
  // Pauli gates
  X: new Matrix([
    [COMPLEX_ZERO, COMPLEX_ONE],
    [COMPLEX_ONE, COMPLEX_ZERO]
  ]),
  
  Y: new Matrix([
    [COMPLEX_ZERO, new Complex(0, -1)],
    [new Complex(0, 1), COMPLEX_ZERO]
  ]),
  
  Z: new Matrix([
    [COMPLEX_ONE, COMPLEX_ZERO],
    [COMPLEX_ZERO, new Complex(-1, 0)]
  ]),
  
  // Hadamard gate
  H: new Matrix([
    [new Complex(1/Math.sqrt(2), 0), new Complex(1/Math.sqrt(2), 0)],
    [new Complex(1/Math.sqrt(2), 0), new Complex(-1/Math.sqrt(2), 0)]
  ]),
  
  // Phase gates
  S: new Matrix([
    [COMPLEX_ONE, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_I]
  ]),
  
  T: new Matrix([
    [COMPLEX_ONE, COMPLEX_ZERO],
    [COMPLEX_ZERO, Complex.fromPolar(1, Math.PI/4)]
  ]),
  
  // Create rotation gates around X, Y, Z axes
  Rx: (theta: number): Matrix => {
    const cos = Math.cos(theta/2);
    const sin = Math.sin(theta/2);
    return new Matrix([
      [new Complex(cos, 0), new Complex(0, -sin)],
      [new Complex(0, -sin), new Complex(cos, 0)]
    ]);
  },
  
  Ry: (theta: number): Matrix => {
    const cos = Math.cos(theta/2);
    const sin = Math.sin(theta/2);
    return new Matrix([
      [new Complex(cos, 0), new Complex(-sin, 0)],
      [new Complex(sin, 0), new Complex(cos, 0)]
    ]);
  },
  
  Rz: (theta: number): Matrix => {
    const phase = theta/2;
    return new Matrix([
      [Complex.fromPolar(1, -phase), COMPLEX_ZERO],
      [COMPLEX_ZERO, Complex.fromPolar(1, phase)]
    ]);
  },
  
  // Two-qubit gates
  CNOT: new Matrix([
    [COMPLEX_ONE, COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_ONE, COMPLEX_ZERO, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ONE],
    [COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ONE, COMPLEX_ZERO]
  ]),
  
  CZ: new Matrix([
    [COMPLEX_ONE, COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_ONE, COMPLEX_ZERO, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ONE, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ZERO, new Complex(-1, 0)]
  ]),
  
  SWAP: new Matrix([
    [COMPLEX_ONE, COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ONE, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_ONE, COMPLEX_ZERO, COMPLEX_ZERO],
    [COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ZERO, COMPLEX_ONE]
  ])
};

// ======== Statistical Functions ========

/**
 * Calculate the mean of an array of numbers
 */
export function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

/**
 * Calculate the variance of an array of numbers
 */
export function variance(values: number[]): number {
  if (values.length <= 1) return 0;
  const avg = mean(values);
  return values.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / (values.length - 1);
}

/**
 * Calculate the standard deviation of an array of numbers
 */
export function standardDeviation(values: number[]): number {
  return Math.sqrt(variance(values));
}

/**
 * Calculate the median of an array of numbers
 */
export function median(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

/**
 * Calculate the binomial probability
 * P(X = k) where X ~ Bin(n, p)
 */
export function binomialProbability(n: number, k: number, p: number): number {
  if (k < 0 || k > n) return 0;
  return binomialCoefficient(n, k) * Math.pow(p, k) * Math.pow(1 - p, n - k);
}

/**
 * Calculate the binomial coefficient (n choose k)
 */
export function binomialCoefficient(n: number, k: number): number {
  if (k < 0 || k > n) return 0;
  if (k === 0 || k === n) return 1;
  
  // Optimize for large numbers
  k = Math.min(k, n - k);
  let result = 1;
  for (let i = 1; i <= k; i++) {
    result *= (n - (k - i));
    result /= i;
  }
  return result;
}

/**
 * Calculate the probability of at most k errors in n trials with error rate p
 * Uses the cumulative binomial distribution
 */
export function errorProbabilityAtMost(n: number, k: number, p: number): number {
  let probability = 0;
  for (let i = 0; i <= k; i++) {
    probability += binomialProbability(n, i, p);
  }
  return probability;
}

/**
 * Calculate the fidelity between two pure quantum states
 * F(|ψ⟩, |φ⟩) = |⟨ψ|φ⟩|²
 */
export function stateFidelity(state1: Complex[], state2: Complex[]): number {
  if (state1.length !== state2.length) {
    throw new Error("States must have the same dimension");
  }
  
  // Calculate inner product ⟨ψ|φ⟩
  let innerProduct = COMPLEX_ZERO;
  for (let i = 0; i < state1.length; i++) {
    innerProduct = innerProduct.add(state1[i].conjugate().multiply(state2[i]));
  }
  
  // Return |⟨ψ|φ⟩|²
  return innerProduct.magnitudeSquared();
}

/**
 * Calculate the trace distance between two density matrices
 * T(ρ, σ) = (1/2) * Tr|ρ - σ|
 * 
 * Note: This is a simplified version that works for pure states
 */
export function traceDistance(state1: Complex[], state2: Complex[]): number {
  const fid = stateFidelity(state1, state2);
  return Math.sqrt(1 - fid);
}

/**
 * Estimate success probability of a quantum circuit with given error rates
 * 
 * @param gateCount Number of gates in the circuit
 * @param gateErrorRate Error rate per gate
 * @param measurementErrorRate Error rate per measurement
 * @param measurements Number of measurements
 */
export function estimateCircuitSuccessProbability(
  gateCount: number,
  gateErrorRate: number,
  measurementErrorRate: number = 0,
  measurements: number = 1
): number {
  // Probability of no errors in gates
  const gateSuccessProbability = Math.pow(1 - gateErrorRate, gateCount);
  
  // Probability of no errors in measurements
  const measurementSuccessProbability = Math.pow(1 - measurementErrorRate, measurements);
  
  // Overall success probability
  return gateSuccessProbability * measurementSuccessProbability;
}

// ======== Quantum-Specific Helper Functions ========

/**
 * Calculate the number of bits needed to represent a number
 */
export function bitsRequired(n: number): number {
  return Math.ceil(Math.log2(n + 1));
}

/**
 * Convert a decimal number to its binary representation
 */
export function decimalToBinary(decimal: number, padLength: number = 0): string {
  const binary = decimal.toString(2);
  return binary.padStart(padLength, '0');
}

/**
 * Convert a binary string to its decimal representation
 */
export function binaryToDecimal(binary: string): number {
  return parseInt(binary, 2);
}

/**
 * Generate all possible bit strings of given length
 */
export function generateBitStrings(length: number): string[] {
  const result: string[] = [];
  const total = Math.pow(2, length);
  
  for (let i = 0; i < total; i++) {
    result.push(decimalToBinary(i, length));
  }
  
  return result;
}

/**
 * Calculate the Hamming weight (number of 1s) in a binary string
 */
export function hammingWeight(binary: string): number {
  return binary.split('').filter(bit => bit === '1').length;
}

/**
 * Calculate the Hamming distance between two binary strings
 */
export function hammingDistance(a: string, b: string): number {
  if (a.length !== b.length) {
    throw new Error("Strings must have equal length");
  }
  
  let distance = 0;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) {
      distance++;
    }
  }
  
  return distance;
}

/**
 * Normalize a quantum state vector
 */
export function normalizeState(state: Complex[]): Complex[] {
  // Calculate the norm
  let normSquared = 0;
  for (const amplitude of state) {
    normSquared += amplitude.magnitudeSquared();
  }
  
  const norm = Math.sqrt(normSquared);
  
  // Normalize
  return state.map(amplitude => amplitude.scale(1 / norm));
}

/**
 * Check if a state vector is normalized
 */
export function isNormalized(state: Complex[], tolerance: number = 1e-10): boolean {
  let normSquared = 0;
  for (const amplitude of state) {
    normSquared += amplitude.magnitudeSquared();
  }
  
  return Math.abs(normSquared - 1) < tolerance;
}

/**
 * Calculate the expectation value of an observable (Hermitian matrix)
 * ⟨ψ|A|ψ⟩
 */
export function expectationValue(state: Complex[], observable: Matrix): Complex {
  if (!observable.isHermitian()) {
    throw new Error("Observable must be Hermitian");
  }
  
  if (state.length !== observable.rows) {
    throw new Error("State dimension must match observable dimension");
  }
  
  // Apply observable to state: A|ψ⟩
  const appliedState = observable.apply(state);
  
  // Calculate ⟨ψ|A|ψ⟩
  let result = COMPLEX_ZERO;
  for (let i = 0; i < state.length; i++) {
    result = result.add(state[i].conjugate().multiply(appliedState[i]));
  }
  
  return result;
}
