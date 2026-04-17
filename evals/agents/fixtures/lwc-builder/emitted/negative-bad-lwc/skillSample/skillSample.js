import { LightningElement } from 'lwc';

// Intentionally broken: does not extend LightningElement and has unbalanced braces.
export default class SkillSample {
    connectedCallback() {
        console.log('broken');
    // missing close brace
}
