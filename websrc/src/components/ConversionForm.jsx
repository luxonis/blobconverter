import React from 'react';
import PropTypes from 'prop-types';

const ConversionForm = () => {
  const [advanced, setAdvanced] = React.useState(false);
  console.log(advanced)
  return (
    <div className={`params-form ${advanced ? 'expanded' : ''}`}>
      <div className="params-form-paths">
        <div className="upper-border">Model parameters</div>
        <div className="form"/>
        <div className="lower-border">
          By submitting this form, you accept our <a href="#">Privacy Policy</a>
        </div>
      </div>
      <div className="params-form-steps"/>
      <div className={`params-form-advanced ${advanced ? 'expanded' : ''}`}>
        <div className="expander" onClick={() => setAdvanced(!advanced)}>
          Advanced >
        </div>
      </div>
    </div>
  );
}

ConversionForm.propTypes = {};

export default React.memo(ConversionForm);
