import { Router } from 'express';
import { healthController, searchController } from '../controllers/searchController.js';
import { validateSearch } from '../middleware/validateSearch.js';

const router = Router();

router.get('/health', healthController);
router.post('/search', validateSearch, searchController);

export default router;
