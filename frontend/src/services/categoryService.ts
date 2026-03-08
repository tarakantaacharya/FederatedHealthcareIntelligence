import api from './api';
import { CategoryInfo, CategoryExtensions } from '../types/categories';

class CategoryService {
  /**
   * Get all category extensions
   */
  async getAllCategories(): Promise<CategoryExtensions> {
    const response = await api.get<CategoryExtensions>('/api/categories/all');
    return response.data;
  }

  /**
   * List category names
   */
  async listCategoryNames(): Promise<string[]> {
    const response = await api.get<string[]>('/api/categories/list');
    return response.data;
  }

  /**
   * Get category info
   */
  async getCategoryInfo(categoryName: string): Promise<CategoryInfo> {
    const response = await api.get<CategoryInfo>(`/api/categories/${categoryName}`);
    return response.data;
  }

  /**
   * Get category fields
   */
  async getCategoryFields(categoryName: string): Promise<Record<string, any>> {
    const response = await api.get(`/api/categories/${categoryName}/fields`);
    return response.data;
  }

  /**
   * Get category field list
   */
  async getCategoryFieldList(categoryName: string): Promise<string[]> {
    const response = await api.get<string[]>(`/api/categories/${categoryName}/field-list`);
    return response.data;
  }

  /**
   * Get category display name
   */
  getCategoryDisplayName(categoryId: string): string {
    const names: Record<string, string> = {
      'icu': 'Intensive Care Unit',
      'emergency': 'Emergency Department',
      'opd': 'Outpatient Department',
      'ipd': 'Inpatient Department',
      'surgery': 'Surgical Department',
      'pediatrics': 'Pediatric Department',
      'cardiology': 'Cardiology Department'
    };
    
    return names[categoryId] || categoryId.toUpperCase();
  }
}

export default new CategoryService();
