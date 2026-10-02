import { Component } from "react";

export default class ViewErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error) {
    console.error("Workspace view failed to load", error);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="qa-content">
          <div className="qa-loading" role="alert">
            <h2>This view could not be loaded</h2>
            <p>
              Reload to get the latest app files, or select another workspace.
              Reloading clears unsaved inputs.
            </p>
            <button
              type="button"
              className="qa-run-button mt-5 mx-auto"
              onClick={() => window.location.reload()}
            >
              Reload workspace
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
