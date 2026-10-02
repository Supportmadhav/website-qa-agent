import React from "react";

import App from "./App";

class BootErrorBoundary extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      error: null,
    };
  }

  static getDerivedStateFromError(error) {
    return {
      error,
    };
  }

  render() {
    if (this.state.error) {
      return (
        <pre
          style={{
            margin: 24,
            whiteSpace: "pre-wrap",
            color: "#9f1239",
            fontFamily: "Segoe UI, sans-serif",
          }}
        >
          {String(this.state.error?.stack || this.state.error)}
        </pre>
      );
    }

    return this.props.children;
  }
}

export default function Workspace() {
  return (
    <BootErrorBoundary>
      <App />
    </BootErrorBoundary>
  );
}
