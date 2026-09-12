import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import ExercisesCatalogPage from "./ExercisesCatalogPage";

const mockList = jest.fn();
const mockSync = jest.fn();
jest.mock("../services/exerciseCatalogService", () => ({
  listExercises: (...args: unknown[]) => mockList(...args),
  syncExerciseDb: (...args: unknown[]) => mockSync(...args),
}));

test("renderiza exercícios e indicador de vínculo Hevy", async () => {
  mockList.mockResolvedValue({ exercises: [{ id: "1", name: "Bench Press", source: "exercisedb", exercisedb_id: "x", hevy_template_id: "h", name_en: "Bench Press", body_part: "chest", target_muscle: "pectorals", secondary_muscles: [], equipment: "barbell", movement_pattern: "push", instructions: null, image_url: null, video_url: null, media_hint: null }], count: 1, offset: 0, limit: 50 });
  render(<BrowserRouter><ExercisesCatalogPage /></BrowserRouter>);
  await waitFor(() => expect(screen.getByText("Bench Press")).toBeInTheDocument());
  expect(screen.getByText("Ligado ao Hevy")).toBeInTheDocument();
});
