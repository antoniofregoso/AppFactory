import { StringField } from './StringField.jsx';
import { PasswordField } from './PasswordField.jsx';
import { IntegerField } from './IntegerField.jsx';
import { DecimalField } from './DecimalField.jsx';
import { MonetaryField } from './MonetaryField.jsx';
import { PercentageField } from './PercentageField.jsx';
import { DateField } from './DateField.jsx';
import { DateTimeField } from './DateTimeField.jsx';
import { BooleanField } from './BooleanField.jsx';
import { ColorField } from './ColorField.jsx';
import { ImageField } from './ImageField.jsx';
import { TextField } from './TextField.jsx';
import { HtmlField } from './HtmlField.jsx';
import { JsonField } from './JsonField.jsx';
import { SelectionField } from './SelectionField.jsx';
import { Many2oneField } from './Many2oneField.jsx';
import { Many2oneAvatarField } from './Many2oneAvatarField.jsx';
import { One2manyField } from './One2manyField.jsx';
import { One2manyFollowersField } from './One2manyFollowersField.jsx';
import { Many2manyField } from './Many2manyField.jsx';
import { Many2manyPillsField } from './Many2manyPillsField.jsx';

const FIELD_COMPONENTS = {
    string: StringField,
    password: PasswordField,
    integer: IntegerField,
    decimal: DecimalField,
    monetary: MonetaryField,
    percentage: PercentageField,
    date: DateField,
    datetime: DateTimeField,
    boolean: BooleanField,
    color: ColorField,
    image: ImageField,
    text: TextField,
    html: HtmlField,
    json: JsonField,
    selection: SelectionField,
    status_badge: SelectionField,
    many2one: Many2oneField,
    many2one_avatar: Many2oneAvatarField,
    one2many: One2manyField,
    one2many_followers: One2manyFollowersField,
    many2many: Many2manyField,
    many2many_pills: Many2manyPillsField,
};

/**
 * Renders the control for a single schema field, dispatching on `field.type`.
 * Every field component shares the same contract:
 *   { field, value, onChange(name, next), lang, readOnly, context }
 * Unknown types fall back to a plain text control.
 */
export function FieldControl(props) {
    const Component = FIELD_COMPONENTS[props.field?.type] ?? StringField;
    return <Component {...props} />;
}
