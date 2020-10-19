import React from 'react';
import ConversionForm from "./ConversionForm";
import {Carousel} from "react-bootstrap";

const Content = () => {
  const [index, setIndex] = React.useState(0);
  return (
    <span>
      <Carousel activeIndex={index} onSelect={console.log} controls={false} indicators={false} keyboard={false}
                touch={false} wrap={false} pause={false} interval={null}>
        <Carousel.Item>
          <ConversionForm/>
        </Carousel.Item>
      </Carousel>
    </span>
  );
}

Content.propTypes = {};

export default React.memo(Content);
