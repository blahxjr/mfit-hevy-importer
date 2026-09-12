import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import WorkoutsPage from "./WorkoutsPage";

const mockList = jest.fn();
jest.mock("../services/workoutEngineService", () => ({ listWorkouts: (...args: unknown[]) => mockList(...args) }));

test("lista treinos locais e permite continuar", async () => {
  mockList.mockResolvedValue({ workouts: [{ id: "w1", name: "Treino A", status: "in_progress", date: "2026-09-11T10:00:00Z", import_id: null, hevy_workout_id: null, hevy_routine_id: null, notes: null, created_at: "", updated_at: "" }] });
  render(<BrowserRouter><WorkoutsPage /></BrowserRouter>);
  await waitFor(() => expect(screen.getByText("Treino A")).toBeInTheDocument());
  expect(screen.getByText("Continuar")).toBeInTheDocument();
});
