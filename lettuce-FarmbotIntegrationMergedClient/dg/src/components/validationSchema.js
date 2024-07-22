import * as Yup from 'yup';

export const registrationSchema = Yup.object().shape({
  name: Yup.string().required('Name is required'),
  password: Yup.string()
      .required('Password is required')
      .min(6, 'Password must be at least 6 characters long'),
  confirmPassword: Yup.string()
      .required('Confirm Password is required')
      .oneOf([Yup.ref('password')], 'Passwords must match')
});

// Existing schemas for seeding and watering jobs can remain as is
export const seedingJobSchema = Yup.object().shape({
  seedType: Yup.string()
      .required('Seed Type is required')
      .oneOf(['Lettuce', 'Raddish', 'Carrot'], 'Invalid Seed Type'),
  seedingDate: Yup.date()
      .required('Seeding Date is required')
      .min(new Date(), 'Seeding Date cannot be in the past'),
  seedingDepth: Yup.number()
      .required('Seeding Depth is required')
      .min(1, 'Seeding Depth must be at least 1 mm')
      .max(100, 'Seeding Depth must be less than or equal to 100 mm'),
  plantDistance: Yup.number()
      .required('Plant Distance is required')
      .min(1, 'Plant Distance must be at least 1 mm')
      .max(1000, 'Plant Distance must be less than or equal to 1000 mm'),
  x0: Yup.number()
      .required('X0 is required')
      .min(0, 'X0 must be at least 0 cm'),
  y0: Yup.number()
      .required('Y0 is required')
      .min(0, 'Y0 must be at least 0 cm'),
  x1: Yup.number()
      .required('X1 is required')
      .min(Yup.ref('x0'), 'X1 must be greater than or equal to X0')
      .max(1000, 'X1 must be less than or equal to 1000 cm'),
  y1: Yup.number()
      .required('Y1 is required')
      .min(Yup.ref('y0'), 'Y1 must be greater than or equal to Y0')
      .max(1000, 'Y1 must be less than or equal to 1000 cm'),
});

export const wateringJobSchema = Yup.object().shape({
  wateringDate: Yup.date()
      .required('Watering Date is required')
      .min(new Date(), 'Watering Date cannot be in the past'),
  Interval: Yup.number()
      .required('Interval is required')
      .min(1, 'Interval must be at least 1 hour'),
  WateringAmount: Yup.number()
      .required('Watering amount is required')
      .min(1, 'Watering amount must be at least 1 ml'),
  height: Yup.number()
      .required('Height is required')
      .min(1, 'Height must be at least 1 cm'),
});
