import {
  type Container,
  type ContainerInterface,
  composeSequential,
  isValidContainer,
} from '@moos/core';

export interface StoredObject {
  id: string;
  shape: ContainerInterface;
  properties: Readonly<Record<string, unknown>>;
}

export interface StoredMorphism {
  id: string;
  source: ContainerInterface;
  target: ContainerInterface;
  container: Container;
  properties: Readonly<Record<string, unknown>>;
}

export interface BootstrapContext {
  system: string;
  messages: string[];
}

export interface ComposedMorphismResult {
  container: Container;
  valid: boolean;
  missingIds: string[];
}

const interfaceSignature = (shape: ContainerInterface): string => {
  const inSig = shape.inputs
    .map((port) => `${port.name}:${port.schema}`)
    .join(',');
  const outSig = shape.outputs
    .map((port) => `${port.name}:${port.schema}`)
    .join(',');
  return `${inSig}->${outSig}`;
};

export class InMemoryCategoryStore {
  private readonly objects = new Map<string, StoredObject>();
  private readonly morphisms = new Map<string, StoredMorphism>();

  upsertObject(entry: StoredObject): void {
    this.objects.set(entry.id, entry);
  }

  upsertMorphism(entry: StoredMorphism): void {
    this.morphisms.set(entry.id, entry);
  }

  getObject(id: string): StoredObject | undefined {
    return this.objects.get(id);
  }

  getMorphism(id: string): StoredMorphism | undefined {
    return this.morphisms.get(id);
  }

  listMorphismIds(): string[] {
    return [...this.morphisms.keys()];
  }

  findMorphismsByInterface(
    source: ContainerInterface,
    target: ContainerInterface,
  ): StoredMorphism[] {
    const sourceSig = interfaceSignature(source);
    const targetSig = interfaceSignature(target);
    return [...this.morphisms.values()].filter(
      (entry) =>
        interfaceSignature(entry.source) === sourceSig &&
        interfaceSignature(entry.target) === targetSig,
    );
  }

  composeBootstrapContext(
    morphismIds: string[],
    system = 'moos-bootstrap',
  ): BootstrapContext {
    const existing = morphismIds
      .map((id) => this.morphisms.get(id))
      .filter((entry): entry is StoredMorphism => Boolean(entry));
    const messages = existing.map((entry) => {
      const provider = String(entry.properties.provider ?? 'unknown');
      return `morphism:${entry.id} provider:${provider}`;
    });
    return {
      system,
      messages,
    };
  }

  composeMorphismChain(morphismIds: string[]): ComposedMorphismResult {
    const known = morphismIds
      .map((id) => this.morphisms.get(id))
      .filter((entry): entry is StoredMorphism => Boolean(entry));
    const missingIds = morphismIds.filter((id) => !this.morphisms.has(id));
    if (known.length === 0) {
      return {
        container: {
          id: 'compose.empty',
          interface: { inputs: [], outputs: [] },
          layers: {},
          wiring: [],
          properties: {},
        },
        valid: false,
        missingIds,
      };
    }
    const composed = known
      .map((entry) => entry.container)
      .slice(1)
      .reduce(
        (accumulator, current) => composeSequential(accumulator, current),
        known[0].container,
      );
    return {
      container: composed,
      valid: isValidContainer(composed) && missingIds.length === 0,
      missingIds,
    };
  }
}
