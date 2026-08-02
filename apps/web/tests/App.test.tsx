import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../src/App";

describe("App", () => {
  it("renders the manual draft room", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "BayesianDraft" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Players" })).toBeInTheDocument();
    expect(screen.getAllByText("Example RB One").length).toBeGreaterThan(1);
  });

  it("records and undoes a pick", () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole("button", { name: "Draft" })[0]);

    expect(screen.getByText("Pick")).toBeInTheDocument();
    expect(screen.getAllByText("Example RB One").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Undo pick" }));

    expect(screen.getByText("No picks yet")).toBeInTheDocument();
  });
});
