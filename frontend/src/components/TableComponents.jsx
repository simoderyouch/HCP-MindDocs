const TableComponent = ({ tablename, data }) => {
    // Splitting data by newline to separate rows
    const rows = data.split('\n');
    
    return (
      <div>
        <h2>{tablename}</h2>
        <table>
          <thead>
            <tr>
              {rows[0].split(',').map((header, index) => (
                <th key={index}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(1).map((row, index) => (
              <tr key={index}>
                {row.split(',').map((cell, index) => (
                  <td key={index}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };


export default  TableComponent