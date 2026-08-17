import { Component, type ErrorInfo, type ReactNode } from "react";

interface PrototypeErrorBoundaryProps {
  children: ReactNode;
}

interface PrototypeErrorBoundaryState {
  error: Error | null;
}

export class PrototypeErrorBoundary extends Component<PrototypeErrorBoundaryProps, PrototypeErrorBoundaryState> {
  state: PrototypeErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): PrototypeErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Gills machine prototype failed closed", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="fatal-error" role="alert">
          <span className="eyebrow">PROTOTYPE STOPPED</span>
          <h1>Machine evidence could not be rendered safely.</h1>
          <p>{this.state.error.message}</p>
        </main>
      );
    }
    return this.props.children;
  }
}
