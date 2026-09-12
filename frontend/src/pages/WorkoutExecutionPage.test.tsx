import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import WorkoutExecutionPage from "./WorkoutExecutionPage";

const mockGet = jest.fn();
const mockLog = jest.fn();
jest.mock("../services/workoutEngineService", () => ({
  getWorkout: (...args: unknown[]) => mockGet(...args),
  logSet: (...args: unknown[]) => mockLog(...args),
  startWorkout: jest.fn(), completeWorkout: jest.fn(), abortWorkout: jest.fn(),
}));

test("exibe exercícios e formulário de série", async () => {
  mockGet.mockResolvedValue({ id: "w1", name: "Treino A", status: "in_progress", date: "2026-09-11T10:00:00Z", import_id: null, hevy_workout_id: null, hevy_routine_id: null, notes: null, created_at: "", updated_at: "", exercises: [{ id: "we1", exercise_id: "e1", exercise_name: "Bench Press", sequence_index: 0, planned_sets: 2, planned_reps: 8, planned_load: "20", planned_time_seconds: null, planned_distance_meters: null, notes: null, set_logs: [] }] });
  render(<MemoryRouter initialEntries={["/workouts/w1"]}><Routes><Route path="/workouts/:workoutId" element={<WorkoutExecutionPage />} /></Routes></MemoryRouter>);
  await waitFor(() => expect(screen.getByText(/Bench Press/)).toBeInTheDocument());
  expect(screen.getByLabelText("Repetições série 1")).toBeInTheDocument();
  expect(screen.getByText("Finalizar treino")).toBeInTheDocument();
});
