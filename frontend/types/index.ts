// frontend/types/index.ts

/**
 * Defines the structure of a Task object returned by the Django API.
 */
export interface Task {
  id: number;
  title: string;
  completed: boolean;
  // Django's DateTimeField is serialized as a string in the API response
  created_at: string; 
}