# Frontend

React/Vite app for the local FibroLens research demo. Requires Node 22.12+ or 24.

From the repository root:

```text
npm --prefix frontend ci
npm --prefix frontend run dev
```

Start the backend separately using the root README. Vite proxies `/api` to
`http://127.0.0.1:8000`; the client defaults to real inference. Upload a DICOM ZIP,
enter questionnaire values and wait for the result. No LLM is connected.

`src/api/adapter.js` maps the backend contract to dashboard props. Numeric codes
are male=0/1 and diabetes=0 no, 1 borderline, 2 yes. Scan previews are actual
backend images. Questionnaire risk is independent of MRI measurements. Fat
clipping warnings and exploratory texture QC remain visible.

```text
npm --prefix frontend run build
npm --prefix frontend run lint
npm --prefix frontend test
```

A production frontend deployment needs a reverse proxy routing `/api` to the
backend; `vite preview` alone does not provide the development proxy. The checked-in
mock data is retained as a development fixture, not used for live results.
