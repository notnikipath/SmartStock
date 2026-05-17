import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

const API = import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8000";

export const fetchHealth = createAsyncThunk("dashboard/fetchHealth", async () => {
  const response = await fetch(`${API}/services/health`);
  if (!response.ok) {
    throw new Error("Cannot load service health");
  }
  return response.json();
});

const slice = createSlice({
  name: "dashboard",
  initialState: {
    language: "ru",
    role: "analyst",
    health: {},
    loading: false,
    error: null,
  },
  reducers: {
    setLanguage(state, action) {
      state.language = action.payload;
    },
    setRole(state, action) {
      state.role = action.payload;
    },
  },
  extraReducers(builder) {
    builder
      .addCase(fetchHealth.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchHealth.fulfilled, (state, action) => {
        state.loading = false;
        state.health = action.payload;
      })
      .addCase(fetchHealth.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || "Unexpected error";
      });
  },
});

export const { setLanguage, setRole } = slice.actions;
export const dashboardReducer = slice.reducer;
