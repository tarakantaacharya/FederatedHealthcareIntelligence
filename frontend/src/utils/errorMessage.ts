export const formatErrorMessage = (
  error: unknown,
  fallback = "An unexpected error occurred."
): string => {
  if (!error) {
    return fallback;
  }

  if (typeof error === "string") {
    return error;
  }

  if (Array.isArray(error)) {
    const messages = error
      .map((item) => formatErrorMessage(item, ""))
      .filter((item) => item);

    return messages.length > 0 ? messages.join("; ") : fallback;
  }

  if (typeof error === "object") {
    // Handle axios errors
    const axiosError = error as any;
    if (axiosError.response?.data) {
      // Try to extract error message from response data
      if (typeof axiosError.response.data === "string") {
        return axiosError.response.data;
      }
      if (axiosError.response.data.detail) {
        return formatErrorMessage(axiosError.response.data.detail);
      }
      if (axiosError.response.data.message) {
        return axiosError.response.data.message;
      }
    }

    // Handle network errors
    if (axiosError.code === "ERR_NETWORK" || axiosError.message?.includes("Network Error")) {
      return "Network error: Unable to connect to server. Please check if the backend is running.";
    }

    const err = error as {
      msg?: unknown;
      message?: unknown;
      detail?: unknown;
    };

    if (typeof err.msg === "string") {
      return err.msg;
    }

    if (typeof err.message === "string") {
      return err.message;
    }

    if (typeof err.detail === "string") {
      return err.detail;
    }

    if (Array.isArray(err.detail)) {
      const messages = err.detail
        .map((item) => formatErrorMessage(item, ""))
        .filter((item) => item);

      return messages.length > 0 ? messages.join("; ") : fallback;
    }
  }

  return fallback;
};
