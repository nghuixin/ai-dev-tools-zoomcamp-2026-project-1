import { createHttpIssueService } from "./httpIssueService";
import type { IssueService } from "./issueService";

export type { IssueService } from "./issueService";
export { ApiError } from "./errors";
export { createHttpIssueService } from "./httpIssueService";
export { createMockIssueService } from "./mockIssueService";

/** Live app uses FastAPI. Keep the mock for tests. */
export const issueService: IssueService = createHttpIssueService();
