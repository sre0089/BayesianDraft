import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { App } from "../src/App";

describe("App", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders the manual draft room", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "BayesianDraft" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Players" })).toBeInTheDocument();
    expect(screen.getAllByText("Example RB One").length).toBeGreaterThan(1);
    expect(screen.getByText(/points over replacement/)).toBeInTheDocument();
  });

  it("records and undoes a pick", () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole("button", { name: "Draft" })[0]);

    expect(screen.getByText("Pick")).toBeInTheDocument();
    expect(screen.getAllByText("Example RB One").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Undo pick" }));

    expect(screen.getByText("No picks yet")).toBeInTheDocument();
  });

  it("saves and restores a draft", () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole("button", { name: "Draft" })[0]);
    fireEvent.click(screen.getByRole("button", { name: "Save draft" }));
    fireEvent.click(screen.getByRole("button", { name: "Undo pick" }));
    fireEvent.click(screen.getByRole("button", { name: "Restore draft" }));

    expect(screen.getAllByText("Example RB One").length).toBeGreaterThan(0);
  });
});
