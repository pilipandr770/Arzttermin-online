# Геолокація та пошук по містах - TerminFinder

## 🎯 Поточна реалізація

### Що працює зараз:

1. **Автокомпліт міст** (`/api/search/cities`)
   - База з 82 найбільших міст Німеччини
   - Пошук при введенні 2+ символів
   - Case-insensitive пошук по початку та вхождению

2. **Геолокація браузера** 
   - Кнопка "Meinen Standort verwenden"
   - HTML5 Geolocation API
   - Reverse geocoding через OpenStreetMap Nominatim
   - Автоматичне заповнення поля міста

3. **Гнучкий пошук по місту**
   - Не тільки exact match, а й частичне співпадіння
   - Пошук в JSON полі address практики
   - Case-insensitive

4. **Підготовка до distance-based search**
   - Practice має поля `latitude` і `longitude`
   - API endpoint `/api/search/cities/nearby` (POST)
   - Функція `calculate_distance()` (Haversine formula)

## 📊 Варіанти покращення

### Варіант 1: Базовий (РЕАЛІЗОВАНО)
**Плюси:**
- ✅ Швидка реалізація
- ✅ Не потребує зовнішніх API ключів
- ✅ Працює офлайн (список міст в константах)
- ✅ Безкоштовно

**Мінуси:**
- ⚠️ Обмежений список міст (82 шт)
- ⚠️ Немає розрахунку відстані
- ⚠️ Nominatim має rate limit (1 req/sec)

**Використання:**
```javascript
// Автокомпліт
fetch('/api/search/cities?q=Münc')
// Відповідь: { cities: ["München"] }

// Геолокація
navigator.geolocation.getCurrentPosition(...)
// → Reverse geocoding → "München"
```

---

### Варіант 2: Google Maps API (НАЙКРАЩИЙ для production)
**Плюси:**
- ✅ Точна геолокація
- ✅ Автокомпліт з усіх адрес (не тільки міста)
- ✅ Розрахунок відстані та часу в дорозі
- ✅ Надійний та швидкий

**Мінуси:**
- ❌ Потребує API ключ
- ❌ Платний (після 28,000 req/month)
- ❌ Складніша інтеграція

**Приклад інтеграції:**
```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places"></script>
<script>
const autocomplete = new google.maps.places.Autocomplete(
    document.getElementById('search-city'),
    { types: ['(cities)'], componentRestrictions: { country: 'de' } }
);

autocomplete.addListener('place_changed', () => {
    const place = autocomplete.getPlace();
    const city = place.name;
    const lat = place.geometry.location.lat();
    const lon = place.geometry.location.lng();
    
    searchDoctors(city, lat, lon);
});
</script>
```

**Ціна:**
- Places Autocomplete: $2.83 per 1000 requests
- Geocoding: $5 per 1000 requests
- Distance Matrix: $5-10 per 1000 requests
- **Free tier:** $200 credit per month (~28,000 requests)

---

### Варіант 3: Mapbox API (АЛЬТЕРНАТИВА)
**Плюси:**
- ✅ Дешевше за Google Maps
- ✅ Гарний UI
- ✅ Geocoding + Distance

**Мінуси:**
- ❌ Менш популярний
- ❌ Потребує API ключ

**Ціна:**
- 100,000 requests/month безкоштовно
- Geocoding: $0.50 per 1000 requests

---

### Варіант 4: PostgreSQL PostGIS (DATABASE-BASED)
**Плюси:**
- ✅ Швидкий пошук по відстані в БД
- ✅ Не потребує зовнішніх API
- ✅ Scalable

**Мінуси:**
- ❌ Потребує PostgreSQL extension PostGIS
- ❌ Треба заповнити координати для всіх практик
- ❌ Складніше SQL запити

**Приклад SQL:**
```sql
-- Enable PostGIS extension
CREATE EXTENSION postgis;

-- Add geography column
ALTER TABLE practices ADD COLUMN location geography(POINT, 4326);

-- Update location from lat/lon
UPDATE practices 
SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE latitude IS NOT NULL;

-- Search doctors within 10km radius
SELECT 
    p.name,
    ST_Distance(p.location, ST_SetSRID(ST_MakePoint(11.576124, 48.137154), 4326)) / 1000 as distance_km
FROM practices p
WHERE ST_DWithin(
    p.location,
    ST_SetSRID(ST_MakePoint(11.576124, 48.137154), 4326)::geography,
    10000  -- 10km in meters
)
ORDER BY distance_km;
```

---

## 🎯 Рекомендація

### Для MVP (зараз):
**Варіант 1** - вже реалізований
- Достатньо для початку
- Безкоштовно
- Працює

### Для Production (later):
**Варіант 2 (Google Maps)** + **Варіант 4 (PostGIS)**
- Google Maps для UI/UX (autocomplete, геолокація)
- PostGIS для швидкого пошуку в радіусі в БД
- Можна додавати поступово

## 📝 TODO для покращення

1. **Заповнити координати практик**
   ```python
   # Можна використати Nominatim для bulk geocoding
   for practice in Practice.query.all():
       if not practice.latitude:
           addr = practice.address_dict
           city = addr.get('city')
           street = addr.get('street')
           # Geocode and update
   ```

2. **Додати фільтр по відстані в UI**
   ```html
   <select id="search-radius">
       <option value="5">5 km</option>
       <option value="10">10 km</option>
       <option value="25" selected>25 km</option>
       <option value="50">50 km</option>
   </select>
   ```

3. **Показувати відстань в результатах**
   ```html
   <span class="badge bg-secondary">
       <i class="bi bi-geo-alt"></i> 3.5 km
   </span>
   ```

4. **Сортування по відстані**
   ```javascript
   // Якщо геолокація включена
   if (userLat && userLon) {
       params.append('sort_by', 'distance');
       params.append('user_lat', userLat);
       params.append('user_lon', userLon);
   }
   ```

## 🔐 Privacy Note

При використанні геолокації важливо:
- ✅ Запитувати дозвіл користувача
- ✅ Пояснювати для чого потрібна геолокація
- ✅ Не зберігати координати без згоди (GDPR)
- ✅ Надавати альтернативу (ручний ввід міста)

## 📚 Ресурси

- [Nominatim API](https://nominatim.org/release-docs/latest/api/Overview/)
- [Google Maps Platform](https://developers.google.com/maps)
- [Mapbox Geocoding](https://docs.mapbox.com/api/search/geocoding/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [Haversine Formula](https://en.wikipedia.org/wiki/Haversine_formula)
