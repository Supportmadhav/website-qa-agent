import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./index.css";


class BootErrorBoundary extends React.Component {
  constructor(
    props
  ) {
    super(
      props
    );

    this.state = {
      error:
        null,
    };
  }

  static getDerivedStateFromError(
    error
  ) {
    return {
      error,
    };
  }

  render() {
    if (
      this.state.error
    ) {
      return (
        <pre
          style={{
            margin: 24,
            whiteSpace: "pre-wrap",
            color: "#9f1239",
            fontFamily: "Segoe UI, sans-serif",
          }}
        >
          {
            String(
              this.state.error?.stack
              ||
              this.state.error
            )
          }
        </pre>
      );
    }

    return this.props.children;
  }
}


ReactDOM
  .createRoot(
    document.getElementById(
      "root"
    )
  )
  .render(
    <React.StrictMode>
      <BootErrorBoundary>
        <App />
      </BootErrorBoundary>
    </React.StrictMode>
  );
