import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Pie, PieChart, Cell } from 'recharts';
import { Calendar, ChevronDown, X, Check } from 'lucide-react';
import '../../styles/Orders.css';

const OrdersAnalytics = () => {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

  // Date states
  const [startDate, setStartDate] = useState('2025-09-01');
  const [endDate, setEndDate] = useState('2025-09-30');
  const [showStartCalendar, setShowStartCalendar] = useState(false);
  const [showEndCalendar, setShowEndCalendar] = useState(false);
  
  // Dropdown states
  const [showCityDropdown, setShowCityDropdown] = useState(false);
  const [showGenderDropdown, setShowGenderDropdown] = useState(false);
  const [showTimeDropdown, setShowTimeDropdown] = useState(false);
  const [showAgeGroupDropdown, setShowAgeGroupDropdown] = useState(false);
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [selectedCities, setSelectedCities] = useState([]);
  const [selectedGenders, setSelectedGenders] = useState([]);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState([]);
  const [selectedTime, setSelectedTime] = useState('Month');
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [availableCities, setAvailableCities] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [topProductsByCategory, setTopProductsByCategory] = useState([]);
  const [categoryPerformance, setCategoryPerformance] = useState([]);
  const [topN, setTopN] = useState(3); //default top 3 categories
    
  // Refs for dropdowns
  const cityDropdownRef = useRef(null);
  const genderDropdownRef = useRef(null);
  const timeDropdownRef = useRef(null);
  const ageGroupDropdownRef = useRef(null);
  const countryDropdownRef = useRef(null);
  const isLoadingRef = useRef(false);
  
  // Constants
  const timeOptions = ['Year', 'Quarter', 'Month', 'Day'];
  const ageGroups = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'];
  
  const [countries, setCountries] = useState([]);

  // Tab states and data
  const [activeTab, setActiveTab] = useState('orders');
  const [filters, setFilters] = useState({
    city: [],
    gender: [],
    dateRange: { start: '2025-01-01', end: '2025-01-31' }
  });
  
  // Data states for API responses
  const [ordersOverTime, setOrdersOverTime] = useState([]);
  const [ordersByLocation, setOrdersByLocation] = useState([]);
  const [ordersByProductCategory, setOrdersByProductCategory] = useState([]);
  const [salesOverTime, setSalesOverTime] = useState([]);
  const [salesByLocation, setSalesByLocation] = useState([]);
  const [salesByProductCategory, setSalesByProductCategory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ordersByDemographics, setOrdersByDemographics] = useState([]);
  const [customerSegmentsByAge, setCustomerSegmentsByAge] = useState([]);
  const [customerSegmentsByGender, setCustomerSegmentsByGender] = useState([]);
  const [customerSegmentsByLocation, setCustomerSegmentsByLocation] = useState([]);
  const [ordersPerRider, setOrdersPerRider] = useState([]);
  const [deliveryPerformance, setDeliveryPerformance] = useState([]);

  // Transform rider data for stacked charts
  const transformRiderData = (data) => {
    const grouped = {};
    data.forEach(item => {
      if (!grouped[item.period]) {
        grouped[item.period] = { period: item.period };
      }
      grouped[item.period][item.courier_name] = item.total_orders || item.avg_delivery_days;
    });
    return Object.values(grouped);
  };

  const ordersPerRiderStacked = useMemo(() => transformRiderData(ordersPerRider), [ordersPerRider]);
  const deliveryPerformanceStacked = useMemo(() => transformRiderData(deliveryPerformance), [deliveryPerformance]);

  // Memoize stats calculations to prevent re-renders
  const ordersStats = React.useMemo(() => [
    { title: 'Total Orders', value: ordersOverTime.reduce((sum, d) => sum + (d.total_orders || 0), 0).toLocaleString() },
    { title: 'Total Items', value: ordersOverTime.reduce((sum, d) => sum + (d.total_items || 0), 0).toLocaleString() },
    { title: 'Unique Customers', value: ordersOverTime.reduce((sum, d) => sum + (d.unique_customers || 0), 0).toLocaleString() }
  ], [ordersOverTime]);

  const salesStats = React.useMemo(() => [
    { title: 'Total Sales', value: '$' + salesOverTime.reduce((sum, d) => sum + (parseFloat(d.total_sales) || 0), 0).toLocaleString() },
    { title: 'Total Orders', value: salesOverTime.reduce((sum, d) => sum + (d.total_orders || 0), 0).toLocaleString() },
    { title: 'Total Items', value: salesOverTime.reduce((sum, d) => sum + (d.total_items || 0), 0).toLocaleString() }
  ], [salesOverTime]);

  const transformDemographicsData = useCallback((data) => {
    const locationMap = {};
    
    data.forEach(item => {
      const location = item.location;
      if (!locationMap[location]) {
        locationMap[location] = { location };
      }
      
      // Create keys like "Male_18-24", "Female_25-34", etc.
      const key = `${item.gender}_${item.age_group}`;
      locationMap[location][key] = item.total_orders;
    });
    
    return Object.values(locationMap);
  }, []);

  const transformedDemographicsData = useMemo(() => 
    transformDemographicsData(ordersByDemographics),
    [ordersByDemographics, transformDemographicsData]
  );

  const customerSegmentsByAgeData = useMemo(() => 
    customerSegmentsByAge.map(item => ({
      name: item.segment,
      value: parseFloat(item.total_revenue) || 0
    })),
    [customerSegmentsByAge]
  );

  const customerSegmentsByGenderData = useMemo(() => 
    customerSegmentsByGender.map(item => ({
      name: item.segment,
      value: parseFloat(item.total_revenue) || 0
    })),
    [customerSegmentsByGender]
  );

  const customerSegmentsByLocationData = useMemo(() => 
    customerSegmentsByLocation.map(item => ({
      name: item.segment,
      value: parseFloat(item.total_revenue) || 0
    })),
    [customerSegmentsByLocation]
  );

  const tabData = {
    orders: {
      title: 'Orders Analytics',
      stats: ordersStats,
      charts: [
        {
          type: 'line',
          title: 'Total Orders Over Time',
          description: `How many orders do we receive each ${selectedTime}?`,
          dataKey: 'total_orders',
          data: ordersOverTime,
          xAxisKey: 'period'
        },
        {
          type: 'bar',
          title: 'Total Orders Per Location',
          description: 'How many orders do we receive in each location?',
          dataKey: 'total_orders',
          data: ordersByLocation,
          xAxisKey: 'location'
        },
        {
          type: 'bar',
          title: 'Total Orders Per Product Category',
          description: `Which product categories generate the most orders?`,
          dataKey: 'total_orders',
          data: ordersByProductCategory,
          xAxisKey: 'category'
        }
      ]
    },
    sales: {
      title: 'Sales Analytics',
      stats: salesStats,
      charts: [
        {
          type: 'line',
          title: 'Total Sales Over Time',
          description: `How many sales have we received each ${selectedTime}?`,
          dataKey: 'total_sales',
          data: salesOverTime,
          xAxisKey: 'period'
        },
        {
          type: 'bar',
          title: 'Total Sales Per Location',
          description: 'How many sales do we receive in each location?',
          dataKey: 'total_sales',
          data: salesByLocation,
          xAxisKey: 'location'
        },
        {
          type: 'bar',
          title: 'Total Sales Per Product Category',
          description: `Which product categories had the most sales?`,
          dataKey: 'total_sales',
          data: salesByProductCategory,
          xAxisKey: 'category'
        }
      ]
    },
    users: {
      title: 'User Statistics',
      stats: [
        { 
          title: 'Total Customers', 
          value: ordersByDemographics.reduce((sum, d) => sum + (d.unique_customers || 0), 0).toLocaleString() || '0'
        },
        { 
          title: 'Total Orders', 
          value: ordersByDemographics.reduce((sum, d) => sum + (d.total_orders || 0), 0).toLocaleString() || '0'
        },
        { 
          title: 'Total Revenue', 
          value: '$' + (customerSegmentsByAge.reduce((sum, d) => sum + (parseFloat(d.total_revenue) || 0), 0).toLocaleString() || '0')
        }
      ],
      charts: [
        {
          type: 'bar',
          title: 'Orders by Demographics',
          description: 'How many orders came from each gender and age group in different locations?',
          dataKey: 'orders',
          data: transformedDemographicsData,
          xAxisKey: 'location',
          isStacked: true
        },
        {
          type: 'pie',
          title: 'Customer Segments by Age Group',
          description: 'Which age group contributes the most to total revenue?',
          dataKey: 'value',
          data: customerSegmentsByAgeData
        },
        {
          type: 'pie',
          title: 'Customer Segments by Gender',
          description: 'Which gender contributes the most to total revenue?',
          dataKey: 'value',
          data: customerSegmentsByGenderData
        },
        {
          type: 'pie',
          title: 'Customer Segments by Location (Top 10)',
          description: 'Which locations contribute the most to total revenue?',
          dataKey: 'value',
          data: customerSegmentsByLocationData
        }
      ]
    },
    products: {
      title: 'Product Trends',
      stats: [
        { 
          title: 'Total Products', 
          value: topProducts.length > 0 
            ? topProducts.reduce((sum, p) => sum + (p.total || 0), 0).toLocaleString()
            : '0'
        },
        { 
          title: 'Top Product Revenue',
          value: topProducts.length > 0 
            ? '$' + (topProducts[0]?.total || 0).toLocaleString()
            : '$0'
        },    
        { 
          title: 'Categories', 
          value: topProductsByCategory.length > 0
            ? [...new Set(topProductsByCategory.map(p => p.category))].length
            : '0'
        }
      ],
      charts: [
        {
          type: 'bar',
          title: 'Top 10 Products by Revenue',
          description: 'Which products generate the most revenue?',
          dataKey: 'total',
          data: topProducts,
          xAxisKey: 'name'
        },
        {
          type: 'bar',
          title: 'Top Products Per Category',
          description: 'Best performing products in each category by revenue',
          dataKey: 'total_revenue',
          data: topProductsByCategory,
          xAxisKey: 'name',
          colorByCategory: true
        },
        {
          type: 'bar',
          title: 'Category Performance Over Time',
          description: `Average order value per category by ${selectedTime}`,
          dataKey: 'avg_order_value',
          data: categoryPerformance,
          xAxisKey: 'period'
        }
      ]
    },
    riders: {
      title: 'Rider Performance',
      stats: [
        { 
          title: 'Total Couriers', 
          value: ordersPerRider.length > 0 
            ? [...new Set(ordersPerRider.map(r => r.courier_name))].length.toLocaleString()
            : '0'
        },
        { 
          title: 'Total Deliveries', 
          value: ordersPerRider.reduce((sum, r) => sum + (r.total_orders || 0), 0).toLocaleString() || '0'
        },
        { 
          title: 'Avg. Delivery Days', 
          value: deliveryPerformance.length > 0
            ? (deliveryPerformance.reduce((sum, r) => sum + (parseFloat(r.avg_delivery_days) || 0), 0) / deliveryPerformance.length).toFixed(1) + ' days'
            : '0 days'
        }
      ],
      charts: [
        {
          type: 'bar',
          title: 'Orders per Rider',
          description: `How many orders were delivered by each courier this ${selectedTime}?`,
          data: ordersPerRiderStacked,
          xAxisKey: 'period',
          isStacked: true
        },
        {
          type: 'bar',
          title: 'Delivery Time Performance',
          description: `What is the average time of order delivery by courier?`,
          data: deliveryPerformanceStacked,
          xAxisKey: 'period',
          isStacked: true
        }
      ]
    }
  };
  
  // API fetch functions
  const fetchOrdersData = useCallback(async () => {
    if (isLoadingRef.current) return; // Prevent duplicate calls
    isLoadingRef.current = true;
    setLoading(true);
    try {
      const timeCategory = selectedTime.toLowerCase();
      
      // Convert selected countries and cities to actual names
      const selectedCountryNames = selectedCountries
        .map(id => countries.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');
      
      const selectedCityNames = selectedCities
        .map(id => availableCities.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');
      
      // Fetch Orders Over Time
      const ordersTimeParams = new URLSearchParams({
        time_granularity: timeCategory,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) ordersTimeParams.append('countries', selectedCountryNames);
      if (selectedCityNames) ordersTimeParams.append('cities', selectedCityNames);
      const ordersTimeRes = await fetch(`${API_BASE_URL}/api/orders/total-orders-over-time?${ordersTimeParams}`);
      const ordersTimeData = await ordersTimeRes.json();
      if (ordersTimeData.success) {
        setOrdersOverTime(ordersTimeData.data);
      }
      
      // Fetch Orders By Location
      const locationType = selectedCityNames ? 'city' : 'country';
      const ordersLocParams = new URLSearchParams({
        type: locationType,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) ordersLocParams.append('countries', selectedCountryNames);
      if (selectedCityNames) ordersLocParams.append('cities', selectedCityNames);
      const ordersLocRes = await fetch(`${API_BASE_URL}/api/orders/total-orders-by-location?${ordersLocParams}`);
      const ordersLocData = await ordersLocRes.json();
      if (ordersLocData.success) {
        setOrdersByLocation(ordersLocData.data);
      }
      
      // Fetch Orders By Product Category
      const ordersCatParams = new URLSearchParams({
        category: timeCategory,
        type: locationType,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) ordersCatParams.append('countries', selectedCountryNames);
      if (selectedCityNames) ordersCatParams.append('cities', selectedCityNames);
      const ordersCatRes = await fetch(`${API_BASE_URL}/api/orders/total-orders-by-product-category?${ordersCatParams}`);
      const ordersCatData = await ordersCatRes.json();
      if (ordersCatData.success) {
        setOrdersByProductCategory(ordersCatData.data);
      }
    } catch (error) {
      console.error('Error fetching orders data:', error);
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  }, [startDate, endDate, selectedTime, selectedCountries, selectedCities, countries, availableCities]);
  
  const fetchSalesData = useCallback(async () => {
    if (isLoadingRef.current) return; // Prevent duplicate calls
    isLoadingRef.current = true;
    setLoading(true);
    try {
      const timeCategory = selectedTime.toLowerCase();
      
      // Convert selected countries and cities to actual names
      const selectedCountryNames = selectedCountries
        .map(id => countries.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');
      
      const selectedCityNames = selectedCities
        .map(id => availableCities.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');
      
      // Fetch Sales Over Time
      const salesTimeParams = new URLSearchParams({
        time_granularity: timeCategory,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) salesTimeParams.append('countries', selectedCountryNames);
      if (selectedCityNames) salesTimeParams.append('cities', selectedCityNames);
      const salesTimeRes = await fetch(`${API_BASE_URL}/api/orders/total-sales-over-time?${salesTimeParams}`);
      const salesTimeData = await salesTimeRes.json();
      if (salesTimeData.success) {
        setSalesOverTime(salesTimeData.data);
      }
      
      // Fetch Sales By Location
      const locationType = selectedCityNames ? 'city' : 'country';
      const salesLocParams = new URLSearchParams({
        type: locationType,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) salesLocParams.append('countries', selectedCountryNames);
      if (selectedCityNames) salesLocParams.append('cities', selectedCityNames);
      const salesLocRes = await fetch(`${API_BASE_URL}/api/orders/total-sales-by-location?${salesLocParams}`);
      const salesLocData = await salesLocRes.json();
      if (salesLocData.success) {
        setSalesByLocation(salesLocData.data);
      }
      
      // Fetch Sales By Product Category
      const salesCatParams = new URLSearchParams({
        category: timeCategory,
        type: locationType,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) salesCatParams.append('countries', selectedCountryNames);
      if (selectedCityNames) salesCatParams.append('cities', selectedCityNames);
      const salesCatRes = await fetch(`${API_BASE_URL}/api/orders/total-sales-by-product-category?${salesCatParams}`);
      const salesCatData = await salesCatRes.json();
      if (salesCatData.success) {
        setSalesByProductCategory(salesCatData.data);
      }
    } catch (error) {
      console.error('Error fetching sales data:', error);
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  }, [startDate, endDate, selectedTime, selectedCountries, selectedCities, countries, availableCities]);

  const fetchCustomerData = useCallback(async () => {
    if (isLoadingRef.current) return; // Prevent duplicate calls
    isLoadingRef.current = true;
    setLoading(true);
    try {
      const selectedCountryNames = selectedCountries
        .map(id => countries.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');
      
      const selectedCityNames = selectedCities
        .map(id => availableCities.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');

      const locationType = selectedCities.length > 0 ? 'city' : 'country';

      // Fetch Orders by Demographics
      const demographicsParams = new URLSearchParams({
        type: locationType,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedGenders.length > 0) {
        demographicsParams.append('gender', selectedGenders.join(','));
      }

      if (selectedAgeGroups.length > 0) {
        selectedAgeGroups.forEach(ageGroup => {
          demographicsParams.append('age_group', ageGroup);
        });
      }

      if (selectedCountryNames) demographicsParams.append('countries', selectedCountryNames);
      if (selectedCityNames) demographicsParams.append('cities', selectedCityNames);
      
      const demographicsRes = await fetch(
        `${API_BASE_URL}/api/customers/orders-by-demographics?${demographicsParams}`
      );
      const demographicsData = await demographicsRes.json();
      if (demographicsData.success) {
        setOrdersByDemographics(demographicsData.data);
      }

      // Fetch Customer Segments by Age
      const segmentsAgeParams = new URLSearchParams({
        segment: 'age',
        start_date: startDate,
        end_date: endDate
      });
      const segmentsAgeRes = await fetch(
        `${API_BASE_URL}/api/customers/segments-revenue?${segmentsAgeParams}`
      );
      const segmentsAgeData = await segmentsAgeRes.json();
      if (segmentsAgeData.success) {
        setCustomerSegmentsByAge(segmentsAgeData.data);
      }

      // Fetch Customer Segments by Gender
      const segmentsGenderParams = new URLSearchParams({
        segment: 'gender',
        start_date: startDate,
        end_date: endDate
      });
      const segmentsGenderRes = await fetch(
        `${API_BASE_URL}/api/customers/segments-revenue?${segmentsGenderParams}`
      );
      const segmentsGenderData = await segmentsGenderRes.json();
      if (segmentsGenderData.success) {
        setCustomerSegmentsByGender(segmentsGenderData.data);
      }

      // Fetch Customer Segments by Location (top 10 only)
      const segmentsLocationParams = new URLSearchParams({
        segment: 'location',
        type: 'country',
        start_date: startDate,
        end_date: endDate
      });
      const segmentsLocationRes = await fetch(
        `${API_BASE_URL}/api/customers/segments-revenue?${segmentsLocationParams}`
      );
      const segmentsLocationData = await segmentsLocationRes.json();
      if (segmentsLocationData.success) {
        // Limit to top 10 locations
        const top10 = segmentsLocationData.data
          .sort((a, b) => parseFloat(b.total_revenue) - parseFloat(a.total_revenue))
          .slice(0, 10);
        setCustomerSegmentsByLocation(top10);
      }

    } catch (error) {
      console.error('Error fetching customer data:', error);
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  }, [startDate, endDate, selectedGenders, selectedAgeGroups, selectedCountries, selectedCities, countries, availableCities]);

  const fetchProductsData = useCallback(async () => {
    if (isLoadingRef.current) return;
    isLoadingRef.current = true;
    setLoading(true);
    try {
      const timeCategory = selectedTime.toLowerCase();
      
      const selectedCountryNames = selectedCountries
        .map(id => countries.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');
      
      const selectedCityNames = selectedCities
        .map(id => availableCities.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');

      // Fetch Top Performing Products (by revenue)
      const topProductsParams = new URLSearchParams({
        metric: 'revenue',
        order: 'DESC',
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) topProductsParams.append('countries', selectedCountryNames);
      if (selectedCityNames) topProductsParams.append('cities', selectedCityNames);
      
      const topProductsRes = await fetch(
        `${API_BASE_URL}/api/products/top-performing?${topProductsParams}`
      );
      const topProductsData = await topProductsRes.json();
      if (topProductsData.success) {
        setTopProducts(topProductsData.data.slice(0, 10));
      }

      // Fetch Top Products Per Category (top 3 per category)
      const topPerCategoryParams = new URLSearchParams({
        metric: 'revenue',
        top_n: topN.toString(),
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) topPerCategoryParams.append('countries', selectedCountryNames);
      if (selectedCityNames) topPerCategoryParams.append('cities', selectedCityNames);
      
      const topPerCategoryRes = await fetch(
        `${API_BASE_URL}/api/products/top-performing-per-category?${topPerCategoryParams}`
      );
      const topPerCategoryData = await topPerCategoryRes.json();
      if (topPerCategoryData.success) {
        setTopProductsByCategory(topPerCategoryData.data);
      }

      // Fetch Category Performance Over Time
      const categoryPerfParams = new URLSearchParams({
        time_granularity: timeCategory,
        start_date: startDate,
        end_date: endDate,
        limit: topN.toString()
      });
      if (selectedCountryNames) categoryPerfParams.append('countries', selectedCountryNames);
      if (selectedCityNames) categoryPerfParams.append('cities', selectedCityNames);
      
      const categoryPerfRes = await fetch(
        `${API_BASE_URL}/api/products/category-performance?${categoryPerfParams}`
      );
      const categoryPerfData = await categoryPerfRes.json();
      if (categoryPerfData.success) {
        setCategoryPerformance(categoryPerfData.data);
      }

    } catch (error) {
      console.error('Error fetching products data:', error);
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  }, [startDate, endDate, selectedTime, selectedCountries, selectedCities, countries, availableCities, topN]);

  const fetchRiderData = useCallback(async () => {
    if (isLoadingRef.current) return; // Prevent duplicate calls
    isLoadingRef.current = true;
    setLoading(true);
    try {
      const timeCategory = selectedTime.toLowerCase();
      
      const selectedCountryNames = selectedCountries
        .map(id => countries.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');
      
      const selectedCityNames = selectedCities
        .map(id => availableCities.find(c => c.id === id)?.name)
        .filter(Boolean)
        .join(',');

      const locationType = selectedCityNames ? 'city' : 'country';

      // Fetch Orders per Rider
      const ordersPerRiderParams = new URLSearchParams({
        time_granularity: timeCategory,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) ordersPerRiderParams.append('countries', selectedCountryNames);
      if (selectedCityNames) ordersPerRiderParams.append('cities', selectedCityNames);
      
      const ordersPerRiderRes = await fetch(
        `${API_BASE_URL}/api/riders/orders-per-rider?${ordersPerRiderParams}`
      );
      const ordersPerRiderData = await ordersPerRiderRes.json();
      if (ordersPerRiderData.success) {
        setOrdersPerRider(ordersPerRiderData.data);
      }

      // Fetch Delivery Performance
      const deliveryPerfParams = new URLSearchParams({
        time_granularity: timeCategory,
        location_type: locationType,
        start_date: startDate,
        end_date: endDate
      });
      if (selectedCountryNames) deliveryPerfParams.append('countries', selectedCountryNames);
      if (selectedCityNames) deliveryPerfParams.append('cities', selectedCityNames);
      
      const deliveryPerfRes = await fetch(
        `${API_BASE_URL}/api/riders/delivery-performance?${deliveryPerfParams}`
      );
      const deliveryPerfData = await deliveryPerfRes.json();
      if (deliveryPerfData.success) {
        setDeliveryPerformance(deliveryPerfData.data);
      }

    } catch (error) {
      console.error('Error fetching rider data:', error);
    } finally {
      setLoading(false);
      isLoadingRef.current = false;
    }
  }, [startDate, endDate, selectedTime, selectedCountries, selectedCities, countries, availableCities]);

  const currentTab = tabData[activeTab];
  const genders = ['Male', 'Female'];

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (cityDropdownRef.current && !cityDropdownRef.current.contains(event.target)) {
        setShowCityDropdown(false);
      }
      if (genderDropdownRef.current && !genderDropdownRef.current.contains(event.target)) {
        setShowGenderDropdown(false);
      }
      if (countryDropdownRef.current && !countryDropdownRef.current.contains(event.target)) {
        setShowCountryDropdown(false);
      }
      if (ageGroupDropdownRef.current && !ageGroupDropdownRef.current.contains(event.target)) {
        setShowAgeGroupDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
}, []);
  
  // fetch dropdown opttions
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/filters/countries`);
        const data = await response.json();
        if (data.success) {
          setCountries(data.data);
        }
      } catch (error) {
        console.error('Error fetching countries:', error);
      }
    };
    
    fetchCountries();
  }, []);

  useEffect(() => {
    const fetchCities = async () => {
      try {
        // When multiple countries are selected, fetch cities for each country
        if (selectedCountries.length > 0) {
          const selectedCountryNames = selectedCountries
            .map(id => countries.find(c => c.id === id)?.name)
            .filter(Boolean);
          
          if (selectedCountryNames.length === 0) return;
          
          // Fetch cities for all selected countries
          const citiesPromises = selectedCountryNames.map(countryName =>
            fetch(`${API_BASE_URL}/api/filters/cities?country=${encodeURIComponent(countryName)}`)
              .then(res => res.json())
          );
          
          const citiesResults = await Promise.all(citiesPromises);
          
          // Combine and deduplicate cities from all countries
          const allCities = citiesResults.flatMap(result => 
            result.success ? result.data : []
          );
          
          const uniqueCities = [];
          const seenCityNames = new Set();
          
          for (const city of allCities) {
            if (!seenCityNames.has(city.name)) {
              seenCityNames.add(city.name);
              uniqueCities.push(city);
            }
          }
          
          setAvailableCities(uniqueCities);
          
          // Clear selected cities that are no longer in the available list
          setSelectedCities(prev => 
            prev.filter(cityId => uniqueCities.some(c => c.id === cityId))
          );
        } else {
          setAvailableCities([]);
          setSelectedCities([]);
        }
      } catch (error) {
        console.error('Error fetching cities:', error);
      }
    };

    fetchCities();
  }, [selectedCountries, countries]);

  // Fetch data on tab change (only on initial mount and tab switch)
  useEffect(() => {
    if (activeTab === 'orders') {
      fetchOrdersData();
    } else if (activeTab === 'sales') {
      fetchSalesData();
    } else if (activeTab === 'users') {
      fetchCustomerData();
    } else if (activeTab === 'riders') {
      fetchRiderData();
    } else if (activeTab === 'products') {
      fetchProductsData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const toggleSelection = (item, selectedItems, setSelectedItems) => {
    setSelectedItems(prev => 
      prev.includes(item)
        ? prev.filter(i => i !== item)
        : [...prev, item]
    );
  };

  const getSelectedText = useCallback((items, isCountry = false) => {
    if (items.length === 0) return 'Select...';

    if (isCountry) {
      if (items.length <= 2) {
        return items
          .map(id => countries.find(c => c.id === id)?.name || id)
          .join(', ');
      }
      return `${items.length} countries selected`;
    }

    if (items.length <= 2) {
      return items
        .map(id => availableCities.find(c => c.id === id)?.name || id)
        .join(', ');
    }
    return `${items.length} cities selected`;
  }, [countries, availableCities]);


  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="header-title">OLAP Analytical Dashboard</h1>
      </header>

      <div className="dashboard-content">
        <aside className="sidebar">
          <h2 className="sidebar-title">Data Navigation</h2>

          <div className="filter-group">
            {/* Start Date Picker */}
            <div className="filter-item">
              <label className="filter-label">Start Date</label>
              <div className="date-picker">
                <input
                  type="text"
                  className="date-input"
                  value={startDate}
                  readOnly
                  onClick={() => setShowStartCalendar(!showStartCalendar)}
                  placeholder="Select start date"
                />
                <Calendar className="calendar-icon" onClick={() => setShowStartCalendar(!showStartCalendar)} />
                {showStartCalendar && (
                  <div className="calendar-dropdown">
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => {
                        setStartDate(e.target.value);
                        setShowStartCalendar(false);
                      }}
                      max={endDate}
                      className="date-input"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* End Date Picker */}
            <div className="filter-item">
              <label className="filter-label">End Date</label>
              <div className="date-picker">
                <input
                  type="text"
                  className="date-input"
                  value={endDate}
                  readOnly
                  onClick={() => setShowEndCalendar(!showEndCalendar)}
                  placeholder="Select end date"
                />
                <Calendar className="calendar-icon" onClick={() => setShowEndCalendar(!showEndCalendar)} />
                {showEndCalendar && (
                  <div className="calendar-dropdown">
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => {
                        setEndDate(e.target.value);
                        setShowEndCalendar(false);
                      }}
                      min={startDate}
                      className="date-input"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Time Granularity Dropdown */}
            <div className="filter-item" ref={timeDropdownRef}>
              <label className="filter-label">Time Granularity</label>
              <div className="dropdown-container">
                <div 
                  className="dropdown-header"
                  onClick={() => setShowTimeDropdown(!showTimeDropdown)}
                >
                  <span>{selectedTime || 'Select...'}</span>
                  <ChevronDown className={`dropdown-arrow ${showTimeDropdown ? 'rotate' : ''}`} />
                </div>
                
                {showTimeDropdown && (
                  <div className="dropdown-options">
                    {timeOptions.map(option => (
                      <div 
                        key={option}
                        className={`dropdown-option ${selectedTime === option ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedTime(option);
                          setShowTimeDropdown(false);
                          setFilters(prev => ({
                            ...prev,
                            timeGranularity: option.toLowerCase()
                          }));
                        }}
                      >
                        <span className="checkbox">
                          {selectedTime === option && <Check size={14} />}
                        </span>
                        {option}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Age Group Dropdown*/}
            {activeTab === 'users' && (
              <div className="filter-item" ref={ageGroupDropdownRef}>
                <label className="filter-label">Age Group</label>
                <div className="dropdown-container">
                  <div 
                    className="dropdown-header"
                    onClick={() => setShowAgeGroupDropdown(!showAgeGroupDropdown)}
                  >
                    <span className={selectedAgeGroups.length === 0 ? 'placeholder' : ''}>
                      {selectedAgeGroups.length === 0 
                        ? 'Select...' 
                        : selectedAgeGroups.length <= 2 
                          ? selectedAgeGroups.join(', ')
                          : `${selectedAgeGroups.length} age groups selected`}
                    </span>
                    <ChevronDown className={`dropdown-arrow ${showAgeGroupDropdown ? 'rotate' : ''}`} />
                  </div>
                  
                  {showAgeGroupDropdown && (
                    <div className="dropdown-options">
                      {ageGroups.map(group => (
                        <div 
                          key={group}
                          className={`dropdown-option ${selectedAgeGroups.includes(group) ? 'selected' : ''}`}
                          onClick={() => toggleSelection(group, selectedAgeGroups, setSelectedAgeGroups)}
                        >
                          <span className="checkbox">
                            {selectedAgeGroups.includes(group) && <Check size={14} />}
                          </span>
                          {group}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Gender Dropdown */}
            {activeTab === 'users' && (
              <div className="filter-item" ref={genderDropdownRef}>
                <label className="filter-label">Gender</label>
                <div className="dropdown-container">
                  <div 
                    className="dropdown-header"
                    onClick={() => setShowGenderDropdown(!showGenderDropdown)}
                  >
                    <span className={selectedGenders.length === 0 ? 'placeholder' : ''}>
                      {getSelectedText(selectedGenders)}
                    </span>
                    <ChevronDown className={`dropdown-arrow ${showGenderDropdown ? 'rotate' : ''}`} />
                  </div>
                  
                  {showGenderDropdown && (
                    <div className="dropdown-options">
                      {genders.map(gender => (
                        <div 
                          key={gender} 
                          className={`dropdown-option ${selectedGenders.includes(gender) ? 'selected' : ''}`}
                          onClick={() => toggleSelection(gender, selectedGenders, setSelectedGenders)}
                        >
                          <span className="checkbox">
                            {selectedGenders.includes(gender) && <Check size={14} />}
                          </span>
                          {gender}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Country Dropdown */}
            <div className="filter-item" ref={countryDropdownRef}>
              <label className="filter-label">Countries</label>
              <div className="dropdown-container">
                <div 
                  className="dropdown-header"
                  onClick={() => setShowCountryDropdown(!showCountryDropdown)}
                >
                  <span className={selectedCountries.length === 0 ? 'placeholder' : ''}>
                    {getSelectedText(selectedCountries, true)}
                  </span>
                  <ChevronDown className={`dropdown-arrow ${showCountryDropdown ? 'rotate' : ''}`} />
                </div>
                
                {showCountryDropdown && (
                  <div className="dropdown-options">
                    {countries.map(country => (
                      <div 
                        key={country.id}
                        className={`dropdown-option ${selectedCountries.includes(country.id) ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedCountries(prev => 
                            prev.includes(country.id)
                              ? prev.filter(id => id !== country.id)
                              : [...prev, country.id]
                          );
                        }}
                      >
                        <span className="checkbox">
                          {selectedCountries.includes(country.id) && <Check size={14} />}
                        </span>
                        {country.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* City Dropdown */}
            <div className="filter-item" ref={cityDropdownRef}>
            <label className="filter-label">Cities</label>
            <div
              className={`dropdown-container ${
                selectedCountries.length === 0 ? 'disabled' : ''
              }`}
            >
              <div
                className="dropdown-header"
                onClick={() => {
                  if (selectedCountries.length === 0) return; // prevent opening
                  setShowCityDropdown(!showCityDropdown);
                }}
              >
                <span
                  className={
                    selectedCities.length === 0
                      ? 'placeholder'
                      : ''
                  }
                >
                  {selectedCountries.length === 0
                    ? 'Select a country first...'
                    : getSelectedText(selectedCities)}
                </span>
                <ChevronDown
                  className={`dropdown-arrow ${
                    showCityDropdown ? 'rotate' : ''
                  }`}
                />
              </div>

              {showCityDropdown && selectedCountries.length > 0 && (
                <div className="dropdown-options">
                  {availableCities.map(city => (
                    <div
                      key={city.id}
                      className={`dropdown-option ${
                        selectedCities.includes(city.id) ? 'selected' : ''
                      }`}
                      onClick={() =>
                        toggleSelection(city.id, selectedCities, setSelectedCities)
                      }
                    >
                      <span className="checkbox">
                        {selectedCities.includes(city.id) && <Check size={14} />}
                      </span>
                      <span>
                        {city.name}
                        {city.country && <span style={{ color: '#888', fontSize: '0.85em', marginLeft: '8px' }}>({city.country})</span>}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Top N Categories Input */}
          {activeTab === 'products' && (
            <div className="filter-item">
              <label className="filter-label">Number of Top Categories</label>
              <input
                type="number"
                className="date-input"
                value={topN}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 5;
                  setTopN(Math.min(Math.max(value, 1), 7)); // limit between 1 and 7
                }}
                min="1"
                max="7"
                placeholder="Enter 1-7"
              />
              <small style={{ color: '#888', fontSize: '0.85em', marginTop: '4px', display: 'block' }}>
                Show top 1-7 categories
              </small>
            </div>
          )}

            {/* Filter Button */}
            <button 
              className="filter-button"
              onClick={() => {
                if (activeTab === 'orders') {
                  fetchOrdersData();
                } else if (activeTab === 'sales') {
                  fetchSalesData();
                } else if (activeTab === 'users') {
                  fetchCustomerData();
                } else if (activeTab === 'riders') {
                  fetchRiderData();
                } else if (activeTab === 'products') {
                  fetchProductsData();
                }
              }}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Filter Results'}
            </button>
          </div>
        </aside>

        <div className="content-wrapper">
          {/* Tabs/buttons at the top */}
          <div className="tabs-container">
            <button
              className={`tab-button orders-tab ${activeTab === 'orders' ? 'active' : ''}`}
              onClick={() => setActiveTab('orders')}
            >
              Orders Analytics
            </button>

            <button
              className={`tab-button sales-tab ${activeTab === 'sales' ? 'active' : ''}`}
              onClick={() => setActiveTab('sales')}
            >
              Sales Analytics
            </button>

            <button
              className={`tab-button users-tab ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              User Statistics
            </button>

            <button
              className={`tab-button products-tab ${activeTab === 'products' ? 'active' : ''}`}
              onClick={() => setActiveTab('products')}
            >
              Product Trends
            </button>

            <button
              className={`tab-button riders-tab ${activeTab === 'riders' ? 'active' : ''}`}
              onClick={() => setActiveTab('riders')}
            >
              Rider Performance
            </button>
          </div>


          <main className={`main-content ${activeTab}-active`}>
            <div className="main-content-container">
              <div className="chart-wrapper">
                <div className="chart-grid">
                  {currentTab.charts.map((chart, index) => (
                    <div key={index} className="chart-card">
                      <div className="chart-header">
                        <h3>{chart.title}</h3>
                        <p>{chart.description}</p>
                      </div>
                      <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                          {chart.type === 'line' ? (
                            <LineChart
                              data={chart.data}
                              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" vertical={false} />
                              <XAxis dataKey={chart.xAxisKey || "date"} />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Line 
                                type="monotone" 
                                dataKey={chart.dataKey} 
                                stroke="#3b82f6" 
                                strokeWidth={2} 
                                dot={false} 
                              />
                            </LineChart>
                          ) : chart.type === 'pie' ? (
                            <PieChart>
                              <Tooltip />
                              <Legend />
                              <Pie
                                data={chart.data}
                                dataKey={chart.dataKey}
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={100}
                                label
                              >
                                {chart.data.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe'][index % 4]} />
                                ))}
                              </Pie>
                            </PieChart>
                          ) : (
                            <BarChart
                              layout={chart.dataKey === 'rating' ? 'vertical' : 'horizontal'}
                              data={chart.data}
                              margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" />
                              {chart.dataKey === 'rating' ? (
                                <>
                                  <XAxis type="number" />
                                  <YAxis dataKey="name" type="category" />
                                </>
                              ) : (
                                <>
                                  <XAxis dataKey={chart.xAxisKey || (chart.data[0] ? Object.keys(chart.data[0])[0] : 'name')} />
                                  <YAxis />
                                </>
                              )}
                              <Tooltip />
                              <Legend />
                              
                              {chart.isStacked && chart.data.length > 0 ? (
                                Object.keys(chart.data[0])
                                  .filter(key => key !== 'location' && key !== chart.xAxisKey)
                                  .map((key, index) => (
                                    <Bar 
                                      key={key}
                                      dataKey={key} 
                                      stackId="a"
                                      fill={['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff'][index % 6]} 
                                    />
                                  ))
                              ) : chart.colorByCategory && chart.data.length > 0 ? (
                                (() => {
                                  const colors = ['#3b82f6', '#CAADFF', '#FFD1E7', '#F7CB81', '#81E6C4', '#06b6d4', '#F1E063'];
                                  // assign colors
                                  const categories = [...new Set(chart.data.map(item => item.category))];
                                  const categoryColors = {};
                                  categories.forEach((cat, idx) => {
                                    categoryColors[cat] = colors[idx % colors.length];
                                  });
                                  
                                  return (
                                    <Bar dataKey={chart.dataKey} radius={[4, 4, 0, 0]}>
                                      {chart.data.map((entry, index) => (
                                        <Cell 
                                          key={`cell-${index}`} 
                                          fill={categoryColors[entry.category]} 
                                        />
                                      ))}
                                    </Bar>
                                  );
                                })()
                              ) : (
                                <Bar 
                                  dataKey={chart.dataKey} 
                                  fill="#3b82f6" 
                                  radius={[4, 4, 0, 0]} 
                                />
                              )}
                            </BarChart>
                          )}
                        </ResponsiveContainer>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </main>
        </div>

      </div>
    </div>
  );
}

export default OrdersAnalytics;