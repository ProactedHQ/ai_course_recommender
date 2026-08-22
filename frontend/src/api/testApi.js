import api from "./axios";

export const pingBackend = async () => {
  const response = await api.get("/");
  return response.data;
};
