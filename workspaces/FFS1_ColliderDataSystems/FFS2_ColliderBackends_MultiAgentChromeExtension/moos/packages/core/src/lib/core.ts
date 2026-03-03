export type JsonSchemaRef = string;

export interface Port {
  name: string;
  schema: JsonSchemaRef;
}

export interface ContainerInterface {
  inputs: Port[];
  outputs: Port[];
}

export interface Wire {
  fromContainerId: string;
  fromPort: string;
  toContainerId: string;
  toPort: string;
}

export interface ContainerLayers {
  rules?: readonly unknown[];
  tools?: readonly unknown[];
  workflows?: readonly unknown[];
  instructions?: readonly unknown[];
  knowledge?: readonly unknown[];
}

export interface Container {
  id: string;
  interface: ContainerInterface;
  layers: ContainerLayers;
  wiring: Wire[];
  properties: Readonly<Record<string, unknown>>;
}

// --- Internal helpers ---

const portKey = (port: Port): string => `${port.name}::${port.schema}`;

const assertNoDuplicatePorts = (ports: Port[], side: string): void => {
  const keys = ports.map(portKey);
  const unique = new Set(keys);
  if (unique.size !== keys.length) {
    throw new Error(`Duplicate ${side} ports are not allowed`);
  }
};

const assertInterfaceValid = (shape: ContainerInterface): void => {
  assertNoDuplicatePorts(shape.inputs, 'inputs');
  assertNoDuplicatePorts(shape.outputs, 'outputs');
};

const arePortsCompatible = (left: Port, right: Port): boolean =>
  left.name === right.name && left.schema === right.schema;

const assertSequentialComposable = (left: Container, right: Container): void => {
  if (left.interface.outputs.length !== right.interface.inputs.length) {
    throw new Error('Sequential composition failed: arity mismatch');
  }
  left.interface.outputs.forEach((outPort, index) => {
    const inPort = right.interface.inputs[index];
    if (!arePortsCompatible(outPort, inPort)) {
      throw new Error(
        `Sequential composition failed: incompatible port ${outPort.name}`,
      );
    }
  });
};

// --- Public API ---

export const createIdentityContainer = (
  id: string,
  shape: ContainerInterface,
): Container => {
  assertInterfaceValid(shape);
  const passthroughWires: Wire[] = shape.inputs.map((input, index) => ({
    fromContainerId: id,
    fromPort: input.name,
    toContainerId: id,
    toPort: shape.outputs[index]?.name ?? input.name,
  }));
  return {
    id,
    interface: {
      inputs: [...shape.inputs],
      outputs: [...shape.outputs],
    },
    layers: {},
    wiring: passthroughWires,
    properties: Object.freeze({ kind: 'identity' }),
  };
};

export const composeSequential = (
  left: Container,
  right: Container,
  id: string = `${left.id}∘${right.id}`,
): Container => {
  assertInterfaceValid(left.interface);
  assertInterfaceValid(right.interface);
  assertSequentialComposable(left, right);
  const bridgeWires: Wire[] = left.interface.outputs.map((outPort, index) => ({
    fromContainerId: left.id,
    fromPort: outPort.name,
    toContainerId: right.id,
    toPort: right.interface.inputs[index].name,
  }));
  return {
    id,
    interface: {
      inputs: [...left.interface.inputs],
      outputs: [...right.interface.outputs],
    },
    layers: {
      workflows: [left.id, right.id],
    },
    wiring: [...left.wiring, ...bridgeWires, ...right.wiring],
    properties: Object.freeze({ kind: 'sequential' }),
  };
};

export const composeParallel = (
  left: Container,
  right: Container,
  id: string = `${left.id}⊗${right.id}`,
): Container => {
  assertInterfaceValid(left.interface);
  assertInterfaceValid(right.interface);
  const prefixedLeftWires = left.wiring.map((wire) => ({
    ...wire,
    fromContainerId: `${left.id}:${wire.fromContainerId}`,
    toContainerId: `${left.id}:${wire.toContainerId}`,
  }));
  const prefixedRightWires = right.wiring.map((wire) => ({
    ...wire,
    fromContainerId: `${right.id}:${wire.fromContainerId}`,
    toContainerId: `${right.id}:${wire.toContainerId}`,
  }));
  const leftInputs = left.interface.inputs.map((port) => ({
    ...port,
    name: `${left.id}.${port.name}`,
  }));
  const rightInputs = right.interface.inputs.map((port) => ({
    ...port,
    name: `${right.id}.${port.name}`,
  }));
  const leftOutputs = left.interface.outputs.map((port) => ({
    ...port,
    name: `${left.id}.${port.name}`,
  }));
  const rightOutputs = right.interface.outputs.map((port) => ({
    ...port,
    name: `${right.id}.${port.name}`,
  }));
  return {
    id,
    interface: {
      inputs: [...leftInputs, ...rightInputs],
      outputs: [...leftOutputs, ...rightOutputs],
    },
    layers: {
      workflows: [left.id, right.id],
    },
    wiring: [...prefixedLeftWires, ...prefixedRightWires],
    properties: Object.freeze({ kind: 'parallel' }),
  };
};

export const isValidContainer = (container: Container): boolean => {
  try {
    assertInterfaceValid(container.interface);
  } catch {
    return false;
  }
  const outputNames = new Set(
    container.interface.outputs.map((port) => port.name),
  );
  const inputNames = new Set(
    container.interface.inputs.map((port) => port.name),
  );
  return container.wiring.every(
    (wire) => outputNames.has(wire.fromPort) || inputNames.has(wire.toPort),
  );
};

export const sameInterface = (left: Container, right: Container): boolean => {
  if (
    left.interface.inputs.length !== right.interface.inputs.length ||
    left.interface.outputs.length !== right.interface.outputs.length
  ) {
    return false;
  }
  const sameInputs = left.interface.inputs.every((port, index) =>
    arePortsCompatible(port, right.interface.inputs[index]),
  );
  const sameOutputs = left.interface.outputs.every((port, index) =>
    arePortsCompatible(port, right.interface.outputs[index]),
  );
  return sameInputs && sameOutputs;
};

export const makeContainer = (
  id: string,
  shape: ContainerInterface,
  properties: Readonly<Record<string, unknown>> = {},
): Container => {
  assertInterfaceValid(shape);
  return {
    id,
    interface: {
      inputs: [...shape.inputs],
      outputs: [...shape.outputs],
    },
    layers: {},
    wiring: [],
    properties,
  };
};
