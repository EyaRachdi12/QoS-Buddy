import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  boAPI,
  dataAPI,
  diagnosticAPI,
  kpiAPI,
  mlAPI,
  getApiError,
} from '../services/api';

const DashboardContext = createContext(null);

export function DashboardProvider({ children }) {
  const [selectedBoId, setSelectedBoId] = useState(null);

  const [overview, setOverview] = useState(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [overviewError, setOverviewError] = useState(null);

  const [kpiPayload, setKpiPayload] = useState({ kpis: [] });
  const [kpiLoading, setKpiLoading] = useState(true);

  const [diagnosticAlerts, setDiagnosticAlerts] = useState([]);
  const [diagnosticSummary, setDiagnosticSummary] = useState(null);
  const [alertsLoading, setAlertsLoading] = useState(true);

  const [detectResult, setDetectResult] = useState(null);
  const [predictResult, setPredictResult] = useState(null);
  const [detectLoading, setDetectLoading] = useState(false);
  const [predictLoading, setPredictLoading] = useState(false);
  const [mlBanner, setMlBanner] = useState(null);

  const [focusedZone, setFocusedZone] = useState(null);

  const [cacheMessage, setCacheMessage] = useState(null);
  const [mlPromptAction, setMlPromptAction] = useState(null);

  /** Per-BO file or unified slice + scoped alerts + cell→city map */
  const [boBundle, setBoBundle] = useState(null);

  /** Counts per source_bo in unified_telecom_dataset_FILLED.csv */
  const [sourceBoSummary, setSourceBoSummary] = useState(null);

  const loadCoreData = useCallback(async () => {
    setOverviewLoading(true);
    setKpiLoading(true);
    setAlertsLoading(true);
    setOverviewError(null);

    try {
      const settled = await Promise.allSettled([
        boAPI.getOverview(24, 120, selectedBoId || null),
        kpiAPI.getRealtimeKPIs(100),
        diagnosticAPI.getLatestAlerts(30),
        diagnosticAPI.getSummary(),
        boAPI.getDashboardBundle(selectedBoId || null, 24),
      ]);

      const [ovSet, kSet, aSet, sSet, bSet] = settled;

      if (ovSet.status === 'fulfilled' && ovSet.value && !ovSet.value.error) {
        setOverview(ovSet.value);
        setOverviewError(null);
      } else {
        setOverview(null);
        const msg =
          ovSet.status === 'fulfilled' && ovSet.value?.error
            ? ovSet.value.error
            : ovSet.status === 'rejected'
              ? getApiError(ovSet.reason)
              : 'Overview unavailable';
        setOverviewError(typeof msg === 'string' ? msg : 'Overview unavailable');
      }

      setKpiPayload(kSet.status === 'fulfilled' ? kSet.value || { kpis: [] } : { kpis: [] });
      setDiagnosticAlerts(aSet.status === 'fulfilled' ? aSet.value?.alerts || [] : []);
      setDiagnosticSummary(
        sSet.status === 'fulfilled' && sSet.value && !sSet.value.error ? sSet.value : null,
      );
      setBoBundle(
        bSet.status === 'fulfilled' && bSet.value && typeof bSet.value === 'object'
          ? bSet.value
          : null,
      );
    } catch (err) {
      setOverview(null);
      setOverviewError(getApiError(err));
      setKpiPayload({ kpis: [] });
      setDiagnosticAlerts([]);
      setDiagnosticSummary(null);
      setBoBundle(null);
    } finally {
      setOverviewLoading(false);
      setKpiLoading(false);
      setAlertsLoading(false);
    }
  }, [selectedBoId]);

  useEffect(() => {
    loadCoreData();
  }, [loadCoreData]);

  useEffect(() => {
    const t = setInterval(loadCoreData, 45000);
    return () => clearInterval(t);
  }, [loadCoreData]);

  useEffect(() => {
    setFocusedZone(null);
    setDetectResult(null);
    setPredictResult(null);
    setMlBanner(null);
    setMlPromptAction(null);
  }, [selectedBoId]);

  const loadSourceBoSummary = useCallback(async () => {
    try {
      const d = await dataAPI.getSourceBoSummary();
      setSourceBoSummary(d && typeof d === 'object' ? d : null);
    } catch {
      setSourceBoSummary(null);
    }
  }, []);

  useEffect(() => {
    loadSourceBoSummary();
  }, [loadSourceBoSummary]);

  const runDetect = useCallback(async () => {
    setDetectLoading(true);
    setDetectResult(null);
    setMlBanner(null);
    try {
      const data = await mlAPI.detect({
        time_window_hours: 24,
        bo_filter: selectedBoId || undefined,
        include_rule_alerts: true,
        max_rows: 8000,
      });
      setDetectResult(data);
      if (data?.success) {
        setMlBanner({ type: 'success', text: 'Detection completed.' });
      } else {
        setMlBanner({
          type: 'warning',
          text: data?.message || 'Detection finished with no data.',
        });
      }
    } catch (err) {
      setDetectResult({ success: false, error: getApiError(err) });
      setMlBanner({ type: 'error', text: getApiError(err) });
    } finally {
      setDetectLoading(false);
    }
  }, [selectedBoId]);

  const runPredict = useCallback(async () => {
    setPredictLoading(true);
    setPredictResult(null);
    setMlBanner(null);
    try {
      const data = await mlAPI.predict({
        target: 'latency_ms',
        time_window_hours: 72,
        bo_filter: selectedBoId || undefined,
        max_train_rows: 25000,
        retrain: true,
      });
      setPredictResult(data);
      if (data?.success) {
        setMlBanner({
          type: 'success',
          text: 'Prediction completed — model metrics updated.',
        });
      } else {
        setMlBanner({
          type: 'warning',
          text: data?.message || 'Prediction did not return results.',
        });
      }
    } catch (err) {
      setPredictResult({ success: false, error: getApiError(err) });
      setMlBanner({ type: 'error', text: getApiError(err) });
    } finally {
      setPredictLoading(false);
    }
  }, [selectedBoId]);

  const refreshDataCache = useCallback(async () => {
    setCacheMessage(null);
    try {
      const data = await mlAPI.refreshData();
      setCacheMessage(
        data?.success
          ? `Cache refreshed: ${data.rows} rows from backend.`
          : 'Refresh returned no rows.',
      );
      await loadSourceBoSummary();
      await loadCoreData();
    } catch (err) {
      setCacheMessage(getApiError(err));
    }
  }, [loadCoreData, loadSourceBoSummary]);

  const runMlOrchestrated = useCallback(
    async (prompt) => {
      const cleanPrompt = String(prompt || '').trim();
      if (!cleanPrompt) {
        setMlBanner({ type: 'warning', text: 'Please write a prompt first.' });
        return null;
      }

      setDetectLoading(true);
      setPredictLoading(true);
      setDetectResult(null);
      setPredictResult(null);
      setMlBanner(null);
      setMlPromptAction(null);

      try {
        const data = await mlAPI.orchestrate({
          prompt: cleanPrompt,
          bo_filter: selectedBoId || undefined,
          detect_time_window_hours: 24,
          predict_time_window_hours: 72,
          include_rule_alerts: true,
          max_detect_rows: 8000,
          max_train_rows: 25000,
          retrain: true,
        });

        const action = data?.action;
        setMlPromptAction(action || null);

        if (action === 'predict') {
          setPredictResult(data?.predict_result || { success: false, message: data?.message });
        } else {
          setDetectResult(data?.detect_result || { success: false, message: data?.message });
        }

        if (data?.success) {
          setMlBanner({
            type: 'success',
            text:
              action === 'predict'
                ? 'Prediction triggered from prompt.'
                : 'Detection triggered from prompt.',
          });
        } else {
          setMlBanner({
            type: 'warning',
            text: data?.message || 'Prompt execution returned no result.',
          });
        }
        return data;
      } catch (err) {
        setMlBanner({ type: 'error', text: getApiError(err) });
        setMlPromptAction(null);
        return null;
      } finally {
        setDetectLoading(false);
        setPredictLoading(false);
      }
    },
    [selectedBoId],
  );

  const mergedAlertsPreview = useMemo(
    () => detectResult?.merged_alerts?.slice(0, 12) || [],
    [detectResult],
  );

  const cellZoneMap = useMemo(() => boBundle?.cell_zone_map || {}, [boBundle]);

  const value = useMemo(
    () => ({
      selectedBoId,
      selectBo: setSelectedBoId,
      overview,
      overviewLoading,
      overviewError,
      refetchOverview: loadCoreData,
      kpiPayload,
      kpiLoading,
      diagnosticAlerts,
      diagnosticSummary,
      alertsLoading,
      boBundle,
      sourceBoSummary,
      cellZoneMap,
      detectResult,
      predictResult,
      detectLoading,
      predictLoading,
      runDetect,
      runPredict,
      runMlOrchestrated,
      mlBanner,
      setMlBanner,
      mlPromptAction,
      focusedZone,
      setFocusedZone,
      mergedAlertsPreview,
      refreshDataCache,
      cacheMessage,
    }),
    [
      selectedBoId,
      overview,
      overviewLoading,
      overviewError,
      loadCoreData,
      kpiPayload,
      kpiLoading,
      diagnosticAlerts,
      diagnosticSummary,
      alertsLoading,
      boBundle,
      sourceBoSummary,
      cellZoneMap,
      detectResult,
      predictResult,
      detectLoading,
      predictLoading,
      runDetect,
      runPredict,
      runMlOrchestrated,
      mlBanner,
      mlPromptAction,
      focusedZone,
      mergedAlertsPreview,
      refreshDataCache,
      cacheMessage,
    ],
  );

  return (
    <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>
  );
}

export function useDashboard() {
  const ctx = useContext(DashboardContext);
  if (!ctx) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }
  return ctx;
}
