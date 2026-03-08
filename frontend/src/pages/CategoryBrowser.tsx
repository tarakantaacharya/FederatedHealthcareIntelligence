import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ConsoleLayout from '../components/ConsoleLayout';
import authService from '../services/authService';
import categoryService from '../services/categoryService';
import { CategoryInfo } from '../types/categories';

const CategoryBrowser: React.FC = () => {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<CategoryInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }

    fetchCategories();
  }, [navigate]);

  const fetchCategories = async () => {
    try {
      const names = await categoryService.listCategoryNames();
      setCategories(names);
      
      // Load first category by default
      if (names.length > 0) {
        loadCategory(names[0]);
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategory = async (categoryName: string) => {
    try {
      const info = await categoryService.getCategoryInfo(categoryName);
      setSelectedCategory(info);
    } catch (error) {
      console.error('Failed to load category:', error);
    }
  };

  return (
    <ConsoleLayout title="Category Browser" subtitle="Canonical category reference">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          Treatment Category Specific Fields
        </h2>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-800">
            <strong>Category Extensions</strong> allow hospitals to track department-specific metrics
            beyond the core canonical schema. Enable categories that match your hospital's departments.
          </p>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading categories...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Category List */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow">
                <div className="px-4 py-3 border-b">
                  <h3 className="font-semibold">Available Categories</h3>
                </div>
                <div className="divide-y">
                  {categories.map((category) => (
                    <button
                      key={category}
                      onClick={() => loadCategory(category)}
                      className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition ${
                        selectedCategory?.category_id === category
                          ? 'bg-primary/10 border-l-4 border-primary'
                          : ''
                      }`}
                    >
                      <p className="font-medium text-sm">
                        {categoryService.getCategoryDisplayName(category)}
                      </p>
                      <p className="text-xs text-gray-500 uppercase mt-1">{category}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Category Details */}
            <div className="lg:col-span-3">
              {selectedCategory ? (
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b">
                    <h3 className="text-xl font-bold">{selectedCategory.name}</h3>
                    <p className="text-sm text-gray-600 mt-1">{selectedCategory.description}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {selectedCategory.num_fields} fields defined
                    </p>
                  </div>

                  <div className="p-6">
                    <h4 className="font-semibold mb-4">Field Definitions</h4>
                    <div className="space-y-4">
                      {Object.entries(selectedCategory.fields).map(([fieldName, fieldSpec]: [string, any]) => (
                        <div key={fieldName} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <p className="font-mono text-sm font-semibold text-primary">
                                {selectedCategory.category_id}_{fieldName}
                              </p>
                              <p className="text-sm text-gray-700 mt-1">{fieldSpec.description}</p>
                            </div>
                            {fieldSpec.required && (
                              <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
                                Required
                              </span>
                            )}
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 text-sm">
                            <div>
                              <p className="text-gray-600">Type</p>
                              <p className="font-semibold">{fieldSpec.type}</p>
                            </div>
                            {fieldSpec.min !== undefined && (
                              <div>
                                <p className="text-gray-600">Min</p>
                                <p className="font-semibold">{fieldSpec.min}</p>
                              </div>
                            )}
                            {fieldSpec.max !== undefined && (
                              <div>
                                <p className="text-gray-600">Max</p>
                                <p className="font-semibold">{fieldSpec.max}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">
                  Select a category to view details
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </ConsoleLayout>
  );
};

export default CategoryBrowser;
