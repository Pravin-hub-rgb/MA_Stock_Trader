import { Typography, Box, Paper } from '@mui/material'

const Results: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Scan Results
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="body1">
          Results browser interface will be implemented here.
          This will allow browsing, downloading, and managing all scan result files.
        </Typography>
      </Paper>
    </Box>
  )
}

export default Results
