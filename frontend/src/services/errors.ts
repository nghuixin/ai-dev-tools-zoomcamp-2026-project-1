export class ApiError extends Error {
  error: string;
  status: number;

  constructor(error: string, status = 400) {
    super(error);
    this.name = "ApiError";
    this.error = error;
    this.status = status;
  }
}
