export interface CategoryField {
  type: string;
  description: string;
  min?: number;
  max?: number;
  required: boolean;
}

export interface CategoryInfo {
  category_id: string;
  name: string;
  description: string;
  num_fields: number;
  fields: Record<string, CategoryField>;
}

export interface CategoryExtensions {
  version: string;
  description: string;
  created_at: string;
  categories: Record<string, any>;
}
